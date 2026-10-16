"""Bounded English image OCR through the fixed official Tesseract CLI."""
from __future__ import annotations

import csv
import hashlib
import io
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import warnings

from agent_sandbox.server import command, start

VERSION = "5.5.0"
PILLOW_VERSION = "11.3.0"
MAX_INPUT = 10 * 1024 * 1024
MAX_PIXELS = 16_000_000
MAX_SIDE = 8192
MAX_TEXT = 1024 * 1024
MAX_TSV = 4 * 1024 * 1024
MAX_DIAGNOSTICS = 1024 * 1024
_JOB_LOCK = threading.Lock()
_LIMIT_EXEC = "import os,resource,sys;resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912));resource.setrlimit(resource.RLIMIT_CPU,(30,31));resource.setrlimit(resource.RLIMIT_FSIZE,(4194304,4194304));os.execve(sys.argv[1],sys.argv[1:],os.environ)"


def _environment() -> dict:
    env = {key: os.environ[key] for key in ("HOME", "PATH", "LD_LIBRARY_PATH") if key in os.environ}
    env.update(LANG="C.UTF-8", LC_ALL="C.UTF-8", OMP_THREAD_LIMIT="1", OMP_NUM_THREADS="1")
    return env


def _process(argv: list[str], *, cwd: str, timeout: float) -> tuple[int, bytes, bytes]:
    """Bound diagnostics; pin the Linux leader until its owned group is stopped."""
    process = subprocess.Popen(argv, cwd=cwd, env=_environment(), stdin=subprocess.DEVNULL,
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
        except OSError:
            pass
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
            time.sleep(.02)
    finally:
        # Never poll/wait/communicate before cleanup: WNOWAIT prevents PID reuse.
        if timed_out:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            grace = time.monotonic() + 1
            while time.monotonic() < grace:
                if os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None:
                    break
                time.sleep(.02)
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            raise RuntimeError("owned OCR process cleanup exceeded its deadline") from None
        for reader in readers:
            reader.join(timeout=2)
    if timed_out:
        raise RuntimeError("OCR process exceeded its wall-clock deadline") from None
    if overflow.is_set():
        raise RuntimeError("OCR process diagnostics exceeded the byte limit") from None
    return process.returncode, b"".join(parts[0]), b"".join(parts[1])


def _binary() -> str:
    value = os.environ.get("OCR_TESSERACT_BINARY", "/usr/bin/tesseract")
    path = Path(value)
    if not path.is_absolute() or not path.is_file() or not os.access(path, os.X_OK):
        raise RuntimeError("the pinned Tesseract executable is unavailable")
    return str(path)


def _tessdata() -> str:
    path = Path(os.environ.get("OCR_TESSDATA_DIR", "/usr/share/tesseract-ocr/5/tessdata"))
    if not path.is_absolute() or not (path / "eng.traineddata").is_file():
        raise RuntimeError("the pinned English traineddata is unavailable")
    return str(path)


def _cli(arguments: list[str], *, cwd: str, timeout: float) -> bytes:
    code, stdout, _ = _process([sys.executable, "-I", "-c", _LIMIT_EXEC, _binary(), *arguments],
                               cwd=cwd, timeout=timeout)
    if code:
        raise RuntimeError("Tesseract exited unsuccessfully; native diagnostics omitted")
    return stdout


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


def _image_bytes(root: Path, descriptor: int, image_path: str) -> bytes:
    if not isinstance(image_path, str) or not image_path or "\x00" in image_path or len(image_path) > 4096:
        raise ValueError("image_path must identify a workspace PNG or JPEG")
    try:
        image_path.encode("utf-8")
    except UnicodeError:
        raise ValueError("image_path must be valid UTF-8") from None
    path = Path(image_path)
    try:
        relative = path.relative_to(root) if path.is_absolute() else path
        if not relative.parts or len(relative.parts) > 32 or ".." in relative.parts:
            raise ValueError
    except ValueError:
        raise ValueError("image_path must stay inside WORKSPACE without symlinks") from None
    parent = os.dup(descriptor)
    image = None
    try:
        for component in relative.parts[:-1]:
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            os.close(parent)
            parent = child
        image = os.open(relative.parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        details = os.fstat(image)
        if not stat.S_ISREG(details.st_mode) or not 0 < details.st_size <= MAX_INPUT:
            raise ValueError("image must be a regular file of at most 10 MiB")
        with os.fdopen(image, "rb") as stream:
            image = None
            data = stream.read(MAX_INPUT + 1)
        if not 0 < len(data) <= MAX_INPUT:
            raise ValueError("image exceeds the encoded byte limit")
        return data
    except OSError:
        raise ValueError("image_path must identify a readable workspace file without symlinks") from None
    finally:
        if image is not None:
            os.close(image)
        os.close(parent)


def _normalize(data: bytes, destination: Path) -> tuple[int, int]:
    from PIL import Image, ImageOps, UnidentifiedImageError, __version__ as pillow_version
    if pillow_version != PILLOW_VERSION:
        raise RuntimeError("Pillow does not match the pinned version")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as image:
                width, height = image.size
                if (image.format not in {"PNG", "JPEG"} or not 1 <= width <= MAX_SIDE or
                        not 1 <= height <= MAX_SIDE or width * height > MAX_PIXELS or getattr(image, "n_frames", 1) != 1):
                    raise ValueError
                image.load()
                oriented = ImageOps.exif_transpose(image)
                rgba = oriented.convert("RGBA")
                normalized = Image.new("RGB", rgba.size, "white")
                normalized.paste(rgba, mask=rgba.getchannel("A"))
                normalized.save(destination, format="PNG")
                if destination.stat().st_size > 64 * 1024 * 1024:
                    raise ValueError
                return normalized.size
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValueError("image must be one valid PNG/JPEG, at most 8192 per side and 16 million pixels") from None


def _read_output(path: Path, limit: int) -> bytes:
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        details = os.fstat(descriptor)
        if not stat.S_ISREG(details.st_mode) or details.st_size > limit:
            raise RuntimeError("OCR output exceeded its file limit")
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            data = stream.read(limit + 1)
        if len(data) > limit:
            raise RuntimeError("OCR output exceeded its byte limit")
        data.decode("utf-8")
        return data
    except (OSError, UnicodeError):
        raise RuntimeError("OCR output is unavailable or invalid UTF-8") from None
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _words(tsv: str, width: int, height: int) -> list[dict]:
    rows = csv.DictReader(io.StringIO(tsv), delimiter="\t", quoting=csv.QUOTE_NONE)
    if rows.fieldnames != "level page_num block_num par_num line_num word_num left top width height conf text".split():
        raise RuntimeError("invalid Tesseract TSV header")
    words = []
    try:
        for index, row in enumerate(rows):
            if index >= 100000 or None in row or any(value is None for value in row.values()):
                raise ValueError
            level = int(row["level"])
            left, top, box_width, box_height = [int(row[name]) for name in ("left", "top", "width", "height")]
            if not 1 <= level <= 5 or min(left, top, box_width, box_height) < 0 or left + box_width > width or top + box_height > height:
                raise ValueError
            if level == 5 and row["text"].strip():
                confidence = float(row["conf"])
                if not 0 <= confidence <= 100:
                    raise ValueError
                words.append({"text": row["text"], "confidence": confidence,
                              "left": left, "top": top, "width": box_width, "height": box_height})
    except (ValueError, TypeError, csv.Error):
        raise RuntimeError("invalid Tesseract TSV content") from None
    return words


def _publish(root: Path, descriptor: int, text: bytes, tsv: bytes) -> dict:
    name = ".ocr-" + uuid.uuid4().hex
    os.mkdir(name, mode=0o700, dir_fd=descriptor)
    directory = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
    try:
        for filename, data in (("text.txt", text), ("words.tsv", tsv)):
            file = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode=0o600, dir_fd=directory)
            with os.fdopen(file, "wb") as stream:
                stream.write(data)
    except BaseException:
        for filename in ("text.txt", "words.tsv"):
            try:
                os.unlink(filename, dir_fd=directory)
            except FileNotFoundError:
                pass
        os.rmdir(name, dir_fd=descriptor)
        raise
    finally:
        os.close(directory)
    return {"artifact_dir": str(root / name), "text_path": str(root / name / "text.txt"),
            "tsv_path": str(root / name / "words.tsv"), "text_sha256": hashlib.sha256(text).hexdigest(),
            "tsv_sha256": hashlib.sha256(tsv).hexdigest()}


@command("ocr_version", description="Read the installed official Tesseract version without a model or network.")
def ocr_version() -> str:
    output = _cli(["--version"], cwd="/tmp", timeout=5).decode("utf-8", "replace").splitlines()
    if not output or output[0] != "tesseract " + VERSION:
        raise RuntimeError("installed Tesseract does not match the pinned version")
    return output[0]


@command("ocr_setup_check", description="Inspect the fixed OCR engine, English language data and Pillow without processing user images.")
def ocr_setup_check() -> dict:
    try:
        version = ocr_version()
        _tessdata()
    except RuntimeError:
        return {"available": False, "pinned_version": VERSION, "language": "eng"}
    from PIL import __version__ as pillow_version
    return {"available": True, "version": version, "pinned_version": VERSION, "pillow_version": pillow_version, "language": "eng"}


@command("ocr", description="Recognize one bounded workspace PNG/JPEG with Tesseract 5.5.0 English; return text and private TXT/TSV artifacts.")
def ocr(image_path: str) -> dict:
    if not _JOB_LOCK.acquire(blocking=False):
        raise RuntimeError("another OCR job is already running")
    descriptor = None
    try:
        root, descriptor = _root()
        data = _image_bytes(root, descriptor, image_path)
        with tempfile.TemporaryDirectory(prefix="abx-ocr-") as temporary:
            private = Path(temporary)
            width, height = _normalize(data, private / "input.png")
            ocr_version()
            _cli([str(private / "input.png"), str(private / "result"), "--tessdata-dir", _tessdata(),
                  "-l", "eng", "--psm", "6", "--dpi", "300", "txt", "tsv"], cwd=temporary, timeout=45)
            text, tsv = _read_output(private / "result.txt", MAX_TEXT), _read_output(private / "result.tsv", MAX_TSV)
            words = _words(tsv.decode(), width, height)
            result = {"text": text.decode(), "word_count": len(words), "width": width, "height": height,
                      "language": "eng", "engine_version": VERSION}
            result.update(_publish(root, descriptor, text, tsv))
            return result
    except OSError:
        raise RuntimeError("OCR workspace/output operation failed; private details omitted") from None
    finally:
        if descriptor is not None:
            os.close(descriptor)
        _JOB_LOCK.release()


@command("ocr_smoke", description="Recognize real high-contrast fixture pixels, independently verify text/TSV artifacts, then remove owned fixtures.")
def ocr_smoke() -> str:
    root, descriptor = _root()
    name = ".ocr-smoke-" + uuid.uuid4().hex + ".png"
    artifact = None
    created = False
    try:
        file = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode=0o600, dir_fd=descriptor)
        created = True
        with os.fdopen(file, "wb") as stream:
            stream.write(Path(__file__).with_name("fixtures").joinpath("sample.png").read_bytes())
        result = ocr(str(root / name))
        artifact = Path(result["artifact_dir"]).name
        directory = os.open(artifact, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
        try:
            with os.fdopen(os.open("text.txt", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory), "rb") as stream:
                text = stream.read(MAX_TEXT + 1)
            with os.fdopen(os.open("words.tsv", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory), "rb") as stream:
                tsv = stream.read(MAX_TSV + 1)
            assert text.decode() == result["text"] and hashlib.sha256(text).hexdigest() == result["text_sha256"]
            assert hashlib.sha256(tsv).hexdigest() == result["tsv_sha256"]
            assert all(word in text.decode().split() for word in ("SANDBOX", "OCR", "314159", "ALPHA", "BETA"))
            rows = list(csv.DictReader(io.StringIO(tsv.decode()), delimiter="\t"))
            observed = {row["text"] for row in rows if row["level"] == "5" and float(row["conf"]) > 50}
            assert {"SANDBOX", "OCR", "314159", "ALPHA", "BETA"} <= observed and result["word_count"] >= 5
        finally:
            for filename in ("text.txt", "words.tsv"):
                os.unlink(filename, dir_fd=directory)
            os.close(directory)
            os.rmdir(artifact, dir_fd=descriptor)
        return "Tesseract image/text/TSV artifacts OK"
    finally:
        if created:
            os.unlink(name, dir_fd=descriptor)
        os.close(descriptor)


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
