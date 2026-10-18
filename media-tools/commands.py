"""Bounded, offline CPU media operations using Debian's pinned FFmpeg tools."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import wave

from agent_sandbox.server import command, start

VERSION = "7.1.5-0+deb13u1"
MAX_FILE = 64 * 1024 * 1024
MAX_DIAGNOSTICS = 1024 * 1024
FORMATS = "mov,matroska,webm,wav,flac,mp3,ogg,avi"
_LOCK = threading.Lock()
_LIMIT_EXEC = ("import os,resource,sys;resource.setrlimit(resource.RLIMIT_CORE,(0,0));"
               "resource.setrlimit(resource.RLIMIT_AS,(1073741824,1073741824));"
               "resource.setrlimit(resource.RLIMIT_CPU,(120,121));"
               "resource.setrlimit(resource.RLIMIT_FSIZE,(67108864,67108864));"
               "os.execve(sys.argv[1],sys.argv[1:],os.environ)")


def _process(argv: list[str], *, cwd: str, timeout: float) -> bytes:
    """Drain bounded output and kill the owned group before reaping its leader."""
    env = {key: os.environ[key] for key in ("HOME", "PATH", "LD_LIBRARY_PATH") if key in os.environ}
    env.update(LANG="C.UTF-8", LC_ALL="C.UTF-8", OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")
    process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    parts: list[list[bytes]] = [[], []]
    overflow = threading.Event()

    def drain(stream, output):
        size = 0
        try:
            while chunk := stream.read(65536):
                if size + len(chunk) <= MAX_DIAGNOSTICS:
                    output.append(chunk)
                    size += len(chunk)
                else:
                    overflow.set()
        finally:
            stream.close()

    readers = [threading.Thread(target=drain, args=(stream, output), daemon=True)
               for stream, output in zip((process.stdout, process.stderr), parts)]
    for reader in readers:
        reader.start()
    deadline = time.monotonic() + timeout
    timed_out = False
    try:
        while os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is None:
            if overflow.is_set():
                break
            if time.monotonic() >= deadline:
                timed_out = True
                break
            time.sleep(.01)
    finally:
        # WNOWAIT anchors the group identity even if the leader already exited.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            raise RuntimeError("owned media process cleanup exceeded its deadline") from None
        for reader in readers:
            reader.join(timeout=2)
    if timed_out:
        raise RuntimeError("media operation exceeded its wall-clock deadline")
    if overflow.is_set():
        raise RuntimeError("media diagnostics exceeded the byte limit")
    if process.returncode:
        raise RuntimeError("media tool failed; native diagnostics omitted")
    return b"".join(parts[0])


def _tool(name: str, arguments: list[str], *, cwd: Path, deadline: float) -> bytes:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise RuntimeError("media operation exceeded its wall-clock deadline")
    return _process([sys.executable, "-I", "-c", _LIMIT_EXEC, "/usr/bin/" + name, *arguments],
                    cwd=str(cwd), timeout=remaining)


def _timeout(command_timeout: int) -> float:
    if type(command_timeout) is not int or not 1 <= command_timeout <= 120:
        raise ValueError("command_timeout must be an integer from 1 to 120 seconds")
    return time.monotonic() + command_timeout


def _root() -> tuple[Path, int]:
    try:
        root = Path(os.environ.get("WORKSPACE") or "/home/user/app").resolve(strict=True)
        descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        if os.fstat(descriptor).st_uid != os.geteuid():
            os.close(descriptor)
            raise ValueError("WORKSPACE must belong to the runtime user")
        return root, descriptor
    except OSError:
        raise ValueError("WORKSPACE must be an existing owned directory") from None


def _snapshot(descriptor: int, input_path: str, destination: Path) -> None:
    if (not isinstance(input_path, str) or not input_path or len(input_path) > 1024
            or "\x00" in input_path or ":" in input_path):
        raise ValueError("input_path must be a relative workspace media file")
    path = Path(input_path)
    if path.is_absolute() or not path.parts or ".." in path.parts or len(path.parts) > 16:
        raise ValueError("input_path must stay inside WORKSPACE without symlinks")
    parent = os.dup(descriptor)
    source = None
    try:
        for part in path.parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            os.close(parent)
            parent = child
        source = os.open(path.parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        details = os.fstat(source)
        if not stat.S_ISREG(details.st_mode) or not 0 < details.st_size <= MAX_FILE:
            raise ValueError("input must be a regular file of at most 64 MiB")
        with os.fdopen(source, "rb") as stream:
            source = None
            data = stream.read(MAX_FILE + 1)
        if not 0 < len(data) <= MAX_FILE:
            raise ValueError("input exceeds the byte limit")
        destination.write_bytes(data)
    except OSError:
        raise ValueError("input_path must identify a readable workspace file without symlinks") from None
    finally:
        if source is not None:
            os.close(source)
        os.close(parent)


def _probe(path: Path, deadline: float) -> dict:
    raw = _tool("ffprobe", ["-v", "error", "-protocol_whitelist", "file", "-format_whitelist", FORMATS,
                            "-show_entries", "format=format_name,duration,size:stream=codec_type,codec_name,width,height,channels,sample_rate",
                            "-of", "json", "-i", str(path)], cwd=path.parent, deadline=deadline)
    try:
        result = json.loads(raw)
        duration = float(result["format"]["duration"])
        streams = result["streams"]
        if not math.isfinite(duration) or not 0 < duration <= 600 or not 1 <= len(streams) <= 8:
            raise ValueError
        for stream in streams:
            if stream["codec_type"] == "video":
                if not 1 <= stream["width"] <= 4096 or not 1 <= stream["height"] <= 2160:
                    raise ValueError
            elif stream["codec_type"] == "audio":
                if not 1 <= stream["channels"] <= 8 or not 1 <= int(stream["sample_rate"]) <= 192000:
                    raise ValueError
            else:
                raise ValueError
        return {"duration_s": duration, "format": result["format"]["format_name"], "streams": streams}
    except (KeyError, TypeError, ValueError):
        raise ValueError("unsupported media: require 1-8 audio/video streams, <=600 seconds, <=4096x2160 and <=8 channels") from None


@command("media_version", description="Inspect the exact installed FFmpeg and ffprobe versions offline.")
def media_version() -> str:
    deadline = _timeout(10)
    for binary in ("ffmpeg", "ffprobe"):
        output = _tool(binary, ["-version"], cwd=Path("/tmp"), deadline=deadline).decode("utf-8", "replace")
        if not output.startswith(binary + " version " + VERSION + " "):
            raise RuntimeError("installed media tools do not match the pinned version")
    return "FFmpeg " + VERSION


@command("media_setup_check", description="Report whether the exact pinned media tools are installed.")
def media_setup_check() -> dict:
    try:
        return {"available": True, "version": media_version()}
    except RuntimeError:
        return {"available": False, "pinned_version": VERSION}


@command("media_probe", description="Inspect one bounded workspace audio/video file without network access.")
def media_probe(input_path: str, command_timeout: int = 30) -> dict:
    deadline = _timeout(command_timeout)
    if not _LOCK.acquire(blocking=False):
        raise RuntimeError("another media operation is active")
    try:
        root, descriptor = _root()
        try:
            with tempfile.TemporaryDirectory(prefix=".media-", dir=root) as directory:
                snapshot = Path(directory) / "input.media"
                _snapshot(descriptor, input_path, snapshot)
                result = _probe(snapshot, deadline)
                return {**result, "bytes": snapshot.stat().st_size}
        finally:
            os.close(descriptor)
    finally:
        _LOCK.release()


@command("transcode", description="Convert a local file to bounded MP4/H.264, WAV or FLAC; never overwrite an artifact.")
def transcode(input_path: str, output_name: str, preset: str = "mp4",
              max_seconds: int = 5, command_timeout: int = 60) -> dict:
    deadline = _timeout(command_timeout)
    if preset not in {"mp4", "wav", "flac"}:
        raise ValueError("preset must be mp4, wav or flac")
    if type(max_seconds) is not int or not 1 <= max_seconds <= 30:
        raise ValueError("max_seconds must be an integer from 1 to 30")
    if not isinstance(output_name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,119}\." + preset, output_name):
        raise ValueError("output_name must be a plain filename with the preset extension")
    if not _LOCK.acquire(blocking=False):
        raise RuntimeError("another media operation is active")
    try:
        root, descriptor = _root()
        try:
            with tempfile.TemporaryDirectory(prefix=".media-", dir=root) as directory:
                job = Path(directory)
                source, output = job / "input.media", job / ("output." + preset)
                _snapshot(descriptor, input_path, source)
                metadata = _probe(source, deadline)
                required = "video" if preset == "mp4" else "audio"
                if not any(stream["codec_type"] == required for stream in metadata["streams"]):
                    raise ValueError("input lacks the stream required by the preset")
                arguments = ["-nostdin", "-v", "error", "-filter_threads", "2", "-threads", "2",
                             "-protocol_whitelist", "file", "-format_whitelist", FORMATS, "-i", str(source),
                             "-t", str(max_seconds), "-map_metadata", "-1", "-map_chapters", "-1"]
                if preset == "mp4":
                    arguments += ["-map", "0:v:0", "-map", "0:a:0?", "-vf", "scale=640:-2,fps=24",
                                  "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                                  "-threads", "2", "-c:a", "aac", "-ac", "2", "-ar", "48000", "-movflags", "+faststart"]
                else:
                    arguments += ["-map", "0:a:0", "-vn", "-c:a", "pcm_s16le" if preset == "wav" else "flac",
                                  "-ac", "1", "-ar", "16000"]
                arguments += ["-fs", str(MAX_FILE), "-n", str(output)]
                _tool("ffmpeg", arguments, cwd=job, deadline=deadline)
                result = _probe(output, deadline)
                size = output.stat().st_size
                if not 0 < size < MAX_FILE or result["duration_s"] > max_seconds + .25:
                    raise RuntimeError("media output exceeded its size or duration limit")
                digest = hashlib.sha256(output.read_bytes()).hexdigest()
                try:
                    os.link(output, output_name, dst_dir_fd=descriptor, follow_symlinks=False)
                except FileExistsError:
                    raise ValueError("output_name already exists; choose a new artifact name") from None
                return {"output_path": str(root / output_name), "bytes": size, "sha256": digest, **result}
        finally:
            os.close(descriptor)
    finally:
        _LOCK.release()


@command("media_smoke", description="Transcode owned synthetic PCM to FLAC, independently decode and compare every sample, then clean up.")
def media_smoke() -> str:
    media_version()
    root, descriptor = _root()
    name = "media-smoke-" + uuid.uuid4().hex
    source = root / (name + ".wav")
    output_name = name + ".flac"
    pcm = b"".join(((index % 160) * 100 - 8000).to_bytes(2, "little", signed=True) for index in range(16000))
    source_created = output_created = False
    try:
        # Exclusive creation and an unpredictable name keep cleanup scoped to this call.
        with source.open("xb") as file:
            source_created = True
            with wave.open(file, "wb") as stream:
                stream.setnchannels(1)
                stream.setsampwidth(2)
                stream.setframerate(16000)
                stream.writeframes(pcm)
        result = transcode(source.name, output_name, preset="flac", max_seconds=1)
        output_created = True
        decoded = _tool("ffmpeg", ["-nostdin", "-v", "error", "-threads", "2", "-protocol_whitelist", "file,pipe",
                                    "-i", str(root / output_name), "-map", "0:a:0", "-f", "s16le", "-c:a", "pcm_s16le", "pipe:1"],
                        cwd=root, deadline=_timeout(20))
        if decoded != pcm or result["streams"][0].get("codec_name") != "flac":
            raise RuntimeError("lossless media self-test failed")
        return "FFmpeg CPU audio transcode OK"
    finally:
        try:
            if source_created:
                os.unlink(source.name, dir_fd=descriptor)
        finally:
            try:
                if output_created:
                    os.unlink(output_name, dir_fd=descriptor)
            finally:
                os.close(descriptor)


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
