"""Actual CPU codecs and real process failure/cleanup, without cloud or model fixtures."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

spec = importlib.util.spec_from_file_location("media_commands_test", Path(__file__).with_name("commands.py"))
media = importlib.util.module_from_spec(spec)
spec.loader.exec_module(media)


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    subprocess.run(["/usr/bin/ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i",
                    "testsrc=size=160x120:rate=12:duration=1", "-f", "lavfi", "-i",
                    "sine=frequency=440:duration=1", "-c:v", "mpeg4", "-threads", "1",
                    "-c:a", "pcm_s16le", str(tmp_path / "input.mkv")], check=True, timeout=20)
    yield tmp_path
    assert not list(tmp_path.glob(".media-*")), "owned temporary jobs must be removed"


def test_actual_pinned_versions():
    assert media.media_version() == "FFmpeg 7.1.5-0+deb13u1"


def test_actual_selftest_cleans_owned_files(workspace):
    assert media.media_smoke() == "FFmpeg CPU audio transcode OK"
    assert not list(workspace.glob("media-smoke-*"))


def test_actual_video_smoke_cleans_owned_files(workspace):
    assert media.media_video_smoke() == "FFmpeg CPU H.264 video transcode OK"
    assert not list(workspace.glob("media-video-*"))


@pytest.mark.parametrize("preset,codec", [("mp4", "h264"), ("wav", "pcm_s16le"), ("flac", "flac")])
def test_actual_transcode_and_independent_probe(workspace, preset, codec):
    result = media.transcode("input.mkv", "converted." + preset, preset=preset, max_seconds=1)
    path = workspace / ("converted." + preset)
    actual = json.loads(subprocess.check_output(["/usr/bin/ffprobe", "-v", "error", "-show_streams",
                                                "-show_format", "-of", "json", str(path)]))
    assert actual["streams"][0]["codec_name"] == codec
    assert .9 <= float(actual["format"]["duration"]) <= 1.2
    if preset == "mp4":
        assert actual["streams"][0]["width"] == 640
        assert actual["streams"][0]["pix_fmt"] == "yuv420p"
    else:
        assert actual["streams"][0]["sample_rate"] == "16000"
        assert actual["streams"][0]["channels"] == 1
    assert result["bytes"] == path.stat().st_size
    assert result["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_probe_actual_streams(workspace):
    result = media.media_probe("input.mkv")
    assert {s["codec_type"] for s in result["streams"]} == {"audio", "video"}
    assert result["bytes"] == (workspace / "input.mkv").stat().st_size


def test_actual_mp4_native_limits_diagnostic(workspace):
    # All inputs are the generated fixture above. Native stderr in this specific
    # regression is safe to disclose and diagnoses platform-dependent allocation.
    arguments = [sys.executable, "-I", "-c", media._LIMIT_EXEC, "/usr/bin/ffmpeg",
                 "-nostdin", "-v", "verbose", "-filter_threads", "2", "-threads", "2",
                 "-protocol_whitelist", "file", "-format_whitelist", media.FORMATS,
                 "-i", str(workspace / "input.mkv"), "-t", "1", "-map_metadata", "-1", "-map_chapters", "-1",
                 "-map", "0:v:0", "-map", "0:a:0?", "-vf", "scale=640:-2,fps=24",
                 "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-threads", "2",
                 "-c:a", "aac", "-ac", "2", "-ar", "48000", "-movflags", "+faststart",
                 "-fs", str(media.MAX_FILE), "-n", str(workspace / "native.mp4")]
    env = {k: os.environ[k] for k in ("HOME", "PATH", "LD_LIBRARY_PATH") if k in os.environ}
    env.update(LANG="C.UTF-8", LC_ALL="C.UTF-8", OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2", MALLOC_ARENA_MAX="2")
    result = subprocess.run(arguments, env=env, capture_output=True, timeout=20)
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")[-3000:]


@pytest.mark.parametrize("input_path", ["../escape.mkv", "/etc/passwd", "https://example.com/a.mp4",
                                         "file:/etc/passwd", "pipe:0", "", "bad\x00name"])
def test_rejects_nonworkspace_input(workspace, input_path):
    with pytest.raises(ValueError):
        media.media_probe(input_path)


@pytest.mark.parametrize("output_name", ["../output.mp4", "/tmp/output.mp4", "-evil.mp4", "out.wav",
                                          "nested/out.mp4", "http:out.mp4", "out.mp4;touch pwned"])
def test_rejects_output_paths_and_argv_injection(workspace, output_name):
    with pytest.raises(ValueError):
        media.transcode("input.mkv", output_name)


def test_symlink_input_and_parent_rejected(workspace):
    (workspace / "alias.mkv").symlink_to(workspace / "input.mkv")
    (workspace / "aliasdir").symlink_to(workspace, target_is_directory=True)
    for path in ("alias.mkv", "aliasdir/input.mkv"):
        with pytest.raises(ValueError):
            media.media_probe(path)


def test_fifo_never_blocks(workspace):
    os.mkfifo(workspace / "fifo")
    with pytest.raises(ValueError, match="regular file"):
        media.media_probe("fifo")


def test_invalid_media_and_playlists_fail(workspace):
    for name, content in (("bad.mp4", b"not media"),
                          ("playlist.m3u8", b"#EXTM3U\n#EXT-X-TARGETDURATION:1\n#EXTINF:1,\nhttps://example.com/a.ts\n")):
        (workspace / name).write_bytes(content)
        with pytest.raises(RuntimeError):
            media.media_probe(name)


def test_oversized_input_rejected(workspace):
    with (workspace / "huge.mkv").open("wb") as stream:
        stream.truncate(media.MAX_FILE + 1)
    with pytest.raises(ValueError, match="64 MiB"):
        media.media_probe("huge.mkv")


def test_existing_file_or_symlink_never_overwritten(workspace):
    path = workspace / "existing.mp4"
    path.write_bytes(b"original")
    (workspace / "alias.mp4").symlink_to(path)
    for output in ("existing.mp4", "alias.mp4"):
        with pytest.raises(ValueError, match="already exists"):
            media.transcode("input.mkv", output)
    assert path.read_bytes() == b"original"
    assert (workspace / "alias.mp4").is_symlink()


def test_missing_required_stream_rejected(workspace):
    media.transcode("input.mkv", "audio.wav", preset="wav")
    subprocess.run(["/usr/bin/ffmpeg", "-nostdin", "-v", "error", "-i", str(workspace / "input.mkv"),
                    "-map", "0:v:0", "-c:v", "copy", str(workspace / "video.mkv")], check=True, timeout=10)
    with pytest.raises(ValueError, match="required"):
        media.transcode("audio.wav", "invalid.mp4")
    with pytest.raises(ValueError, match="required"):
        media.transcode("video.mkv", "invalid.wav", preset="wav")
    assert not list(workspace.glob("invalid.*"))


def test_selftest_failure_still_cleans_source_and_output(workspace, monkeypatch):
    original = media._tool
    def fail_decode(name, arguments, **kwargs):
        if "pipe:1" in arguments:
            raise RuntimeError("synthetic decoder failure after output publication")
        return original(name, arguments, **kwargs)
    monkeypatch.setattr(media, "_tool", fail_decode)
    with pytest.raises(RuntimeError, match="synthetic decoder"):
        media.media_smoke()
    assert not list(workspace.glob("media-smoke-*"))


@pytest.mark.parametrize("arguments", [{"max_seconds": 0}, {"max_seconds": 31}, {"max_seconds": True},
                                          {"command_timeout": 0}, {"command_timeout": 121},
                                          {"command_timeout": True}, {"preset": "shell"}])
def test_invalid_limits_fail(workspace, arguments):
    with pytest.raises(ValueError):
        media.transcode("input.mkv", "output.mp4", **arguments)


def test_concurrent_work_refused(workspace):
    media._LOCK.acquire()
    try:
        with pytest.raises(RuntimeError, match="active"):
            media.media_probe("input.mkv")
        with pytest.raises(RuntimeError, match="active"):
            media.transcode("input.mkv", "out.mp4")
    finally:
        media._LOCK.release()


def test_actual_nonzero_and_diagnostic_overflow(workspace):
    with pytest.raises(RuntimeError, match="tool failed"):
        media._process([sys.executable, "-c", "raise SystemExit(7)"], cwd=str(workspace), timeout=2)
    with pytest.raises(RuntimeError, match="byte limit"):
        media._process([sys.executable, "-c", "import sys;sys.stdout.write('X'*3000000)"], cwd=str(workspace), timeout=2)


@pytest.mark.parametrize("mode", ["success", "failure", "timeout"])
def test_redirected_descendants_killed(workspace, mode):
    pidfile = workspace / "child.pid"
    script = """import subprocess,sys,time
p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
open(sys.argv[1],'w').write(str(p.pid))
if sys.argv[2]=='timeout':time.sleep(60)
if sys.argv[2]=='failure':raise SystemExit(7)
"""
    arguments = [sys.executable, "-c", script, str(pidfile), mode]
    if mode == "success":
        media._process(arguments, cwd=str(workspace), timeout=2)
    else:
        with pytest.raises(RuntimeError):
            media._process(arguments, cwd=str(workspace), timeout=.5)
    child = int(pidfile.read_text())
    for _ in range(100):
        try:
            state = Path(f"/proc/{child}/stat").read_text().split(") ", 1)[1].split()[0]
        except (FileNotFoundError, ProcessLookupError):
            break
        if state == "Z":
            break
        time.sleep(.01)
    else:
        os.kill(child, 9)
        pytest.fail("owned redirected descendant remained active")


def test_environment_does_not_forward_tokens(workspace, monkeypatch):
    monkeypatch.setenv("ABX_LLM_API_KEY", "synthetic-secret")
    output = media._process([sys.executable, "-c", "import os;print('ABX_LLM_API_KEY' in os.environ)"],
                            cwd=str(workspace), timeout=2)
    assert output == b"False\n"


def test_native_array_preserves_spaced_input_and_returns_real_result(workspace):
    (workspace / "literal file.mkv").write_bytes((workspace / "input.mkv").read_bytes())
    result = media.transcode_args(["-i", "literal file.mkv", "-c:a", "flac", "-vn", "-t", "1", "native.flac"])
    assert result["exit_code"] == 0
    assert isinstance(result["stdout"], str) and isinstance(result["stderr"], str)
    path = workspace / "native.flac"
    actual = json.loads(subprocess.check_output(["/usr/bin/ffprobe", "-v", "error", "-show_streams", "-of", "json", str(path)]))
    assert actual["streams"][0]["codec_name"] == "flac"
    assert result["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_native_array_failure_returns_real_exit_without_publishing_partial(workspace):
    # Valid, bounded options; odd YUV420 dimensions are rejected by native libx264.
    result = media.transcode_args(["-i", "input.mkv", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-vf", "scale=63:63", "-an", "bad-native.mp4"])
    assert result["exit_code"] != 0
    assert "divisible by 2" in result["stderr"]
    assert not (workspace / "bad-native.mp4").exists()


@pytest.mark.parametrize("args", [
    '["-i","input.mkv","x.wav"]', ["-i", "input.mkv", 1],
    ["-i", "https://example.com/file.mkv", "x.wav"],
    ["-i", "../input.mkv", "x.wav"], ["-i", "input.mkv", "../x.wav"],
    ["-i", "input.mkv", "-y", "x.wav"], ["-i", "input.mkv", "-i", "input.mkv", "x.wav"],
    ["-i", "input.mkv", "-vf", "movie=/etc/passwd", "x.mp4"],
    ["-i", "input.mkv", "-t", "nan", "x.wav"],
    ["-i", "input.mkv", "-t", "31", "x.wav"],
    ["-i", "input.mkv", "-ac", "8", "x.wav"],
    ["-i", "input.mkv", "-vf", "scale=9999:9999", "x.mp4"],
])
def test_native_array_rejects_unsafe_or_unbounded_options(workspace, args):
    with pytest.raises(ValueError):
        media.transcode_args(args)
    assert not list(workspace.glob("x.*"))


def test_native_array_existing_output_unchanged(workspace):
    (workspace / "existing.flac").write_bytes(b"keep")
    with pytest.raises(ValueError, match="already exists"):
        media.transcode_args(["-i", "input.mkv", "-c:a", "flac", "-vn", "existing.flac"])
    assert (workspace / "existing.flac").read_bytes() == b"keep"


def test_native_argv_smoke_compares_all_pcm_samples_and_cleans(workspace):
    assert media.media_args_smoke() == "FFmpeg native argv audio transcode OK"
    assert not list(workspace.glob("media-smoke-*"))
