"""Actual pinned Pandoc conversion and native process/path regressions."""
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import time
import zipfile
from xml.etree import ElementTree

import pytest

spec = importlib.util.spec_from_file_location("document_commands_test", Path(__file__).with_name("commands.py"))
document = importlib.util.module_from_spec(spec)
spec.loader.exec_module(document)


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    (tmp_path / "source.md").write_text("# Independent document\n\nHello **strong text** 世界.\n\n- Alpha\n- Beta\n", encoding="utf-8")
    yield tmp_path
    assert not list(tmp_path.glob(".document-*")), "private conversion jobs must be removed"


def test_actual_pinned_version():
    assert document.document_version() == "pandoc 3.1.11.1"


@pytest.mark.parametrize("inherited_stack", [8 * 1024 * 1024, 256 * 1024 * 1024])
def test_actual_native_version_resource_limits_diagnostic(inherited_stack):
    # Version-only input contains no user document; retain its native diagnostic
    # to explain platform-specific GHC startup failures without exposing data.
    binary = os.environ.get("DOCUMENT_PANDOC_BINARY", "/usr/bin/pandoc")
    env = {k: os.environ[k] for k in ("HOME", "PATH", "LD_LIBRARY_PATH") if k in os.environ}
    env.update(LANG="C.UTF-8", LC_ALL="C.UTF-8", MALLOC_ARENA_MAX="2",
               pandoc_datadir=os.environ.get("DOCUMENT_PANDOC_DATA_DIR", "/usr/share/pandoc"))
    prefix = ("import resource;_test_stack_hard=resource.getrlimit(resource.RLIMIT_STACK)[1];"
              f"resource.setrlimit(resource.RLIMIT_STACK,(min({inherited_stack},_test_stack_hard) "
              f"if _test_stack_hard>=0 else {inherited_stack},_test_stack_hard));")
    result = subprocess.run([sys.executable, "-I", "-c", prefix + document._LIMIT_EXEC, binary,
                             "--version", "+RTS", "-N2", "-M256M", "-RTS"],
                            env=env, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")[-3000:]


def test_operator_binary_with_wrong_version_refused(workspace, monkeypatch):
    monkeypatch.setenv("DOCUMENT_PANDOC_BINARY", "/bin/echo")
    with pytest.raises(RuntimeError, match="pinned version"):
        document.convert("source.md", "out.docx")
    assert not (workspace / "out.docx").exists()


@pytest.mark.parametrize("input_path", ["../private.md", "https://example.com/input.md", "file:/private.md"])
def test_path_validation_does_not_require_native_engine(workspace, monkeypatch, input_path):
    monkeypatch.setenv("DOCUMENT_PANDOC_BINARY", "/document-tools-no-native-engine")
    with pytest.raises(ValueError):
        document.convert(input_path, "out.docx")
    assert not (workspace / "out.docx").exists()


@pytest.mark.parametrize("output_format", ["docx", "txt"])
def test_actual_conversion_independent_content_and_hash(workspace, output_format):
    original = (workspace / "source.md").read_bytes()
    result = document.convert("source.md", "result." + output_format, output_format=output_format)
    data = (workspace / ("result." + output_format)).read_bytes()
    assert result["bytes"] == len(data) and result["sha256"] == hashlib.sha256(data).hexdigest()
    if output_format == "docx":
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            tree = ElementTree.fromstring(archive.read("word/document.xml"))
            text = "".join(tree.itertext())
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            assert tree.find(".//w:b", ns) is not None
            assert tree.find(".//w:pStyle[@w:val='Heading1']", ns) is not None
    else:
        text = data.decode("utf-8")
        assert "**" not in text and "# Independent" not in text
    assert all(word in text for word in ("Independent document", "strong text", "世界", "Alpha", "Beta"))
    assert (workspace / "source.md").read_bytes() == original


def test_actual_smoke_cleans_every_owned_file(workspace):
    assert document.document_smoke() == "Pandoc Markdown DOCX/TXT artifacts OK"
    assert not list(workspace.glob("document-smoke-*"))


def test_smoke_failure_and_missing_source_still_clean_outputs(workspace, monkeypatch):
    original = document.convert
    def remove_source_after_docx(input_path, output_name, **kwargs):
        result = original(input_path, output_name, **kwargs)
        (workspace / input_path).unlink()
        return result
    monkeypatch.setattr(document, "convert", remove_source_after_docx)
    with pytest.raises(ValueError, match="readable"):
        document.document_smoke()
    assert not list(workspace.glob("document-smoke-*"))


@pytest.mark.parametrize("input_path", ["../source.md", "/etc/passwd", "https://example.com/input.md", "file:/etc/passwd", "", "bad\x00path"])
def test_rejects_nonworkspace_input(workspace, input_path):
    with pytest.raises(ValueError):
        document.convert(input_path, "result.txt", output_format="txt")


@pytest.mark.parametrize("name", ["../out.docx", "/tmp/out.docx", "-evil.docx", "nested/out.docx", "file:out.docx", "out.docx;touch pwned", "wrong.txt"])
def test_rejects_output_paths_and_argv_injection(workspace, name):
    with pytest.raises(ValueError):
        document.convert("source.md", name)


def test_symlink_parents_fifo_and_oversized_inputs(workspace):
    (workspace / "alias.md").symlink_to(workspace / "source.md")
    (workspace / "aliasdir").symlink_to(workspace, target_is_directory=True)
    os.mkfifo(workspace / "fifo")
    with (workspace / "huge.md").open("wb") as stream:
        stream.truncate(document.MAX_FILE + 1)
    for filename in ("alias.md", "aliasdir/source.md", "fifo", "huge.md"):
        with pytest.raises(ValueError):
            document.convert(filename, "out.docx")


@pytest.mark.parametrize("data", [b"", b"   \n", b"binary\x00content", b"bad\xffutf8"])
def test_invalid_document_bytes_rejected(workspace, data):
    (workspace / "bad.md").write_bytes(data)
    with pytest.raises(ValueError):
        document.convert("bad.md", "out.docx")


@pytest.mark.parametrize("content", ["![secret](/etc/passwd)", "![remote](https://example.com/image.png)",
                                       "![data](data:image/png;base64,AAAA)", "[unsafe](javascript:alert(1))",
                                       "[local](file:///etc/passwd)", "[relative](secrets.txt)"])
def test_images_and_nonweb_links_never_reach_docx_writer(workspace, content):
    (workspace / "unsafe.md").write_text(content)
    with pytest.raises((ValueError, RuntimeError)):
        document.convert("unsafe.md", "result.docx")
    assert not (workspace / "result.docx").exists()


def test_raw_html_rejected_before_writer(workspace):
    (workspace / "raw.md").write_text('<script>alert("unsafe")</script>\n\n<iframe src="file:///etc/passwd"></iframe>\n')
    with pytest.raises(ValueError, match="raw nodes"):
        document.convert("raw.md", "safe.txt", output_format="txt")
    assert not (workspace / "safe.txt").exists()


def test_existing_file_and_symlink_never_overwritten(workspace):
    (workspace / "existing.docx").write_bytes(b"original")
    (workspace / "alias.docx").symlink_to(workspace / "existing.docx")
    for filename in ("existing.docx", "alias.docx"):
        with pytest.raises(ValueError, match="already exists"):
            document.convert("source.md", filename)
    assert (workspace / "existing.docx").read_bytes() == b"original"


@pytest.mark.parametrize("arguments", [{"command_timeout": 0}, {"command_timeout": 61}, {"command_timeout": True}, {"output_format": "pdf"}])
def test_limits_and_unimplemented_formats_fail_explicitly(workspace, arguments):
    with pytest.raises(ValueError):
        document.convert("source.md", "result.docx", **arguments)


def test_concurrent_conversion_refused(workspace):
    document._LOCK.acquire()
    try:
        with pytest.raises(RuntimeError, match="active"):
            document.convert("source.md", "result.docx")
    finally:
        document._LOCK.release()


@pytest.mark.parametrize("mode", ["success", "failure", "timeout"])
def test_redirected_descendants_killed(workspace, mode):
    path = workspace / "child.pid"
    source = """import subprocess,sys,time
p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
open(sys.argv[1],'w').write(str(p.pid))
if sys.argv[2]=='timeout':time.sleep(60)
if sys.argv[2]=='failure':raise SystemExit(7)
"""
    argv = [sys.executable, "-c", source, str(path), mode]
    if mode == "success":
        document._process(argv, cwd=str(workspace), timeout=2)
    else:
        with pytest.raises(RuntimeError):
            document._process(argv, cwd=str(workspace), timeout=.5)
    child = int(path.read_text())
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


def test_native_diagnostic_overflow_and_secret_environment(workspace, monkeypatch):
    with pytest.raises(RuntimeError, match="byte limit"):
        document._process([sys.executable, "-c", "print('X'*3000000)"], cwd=str(workspace), timeout=2)
    monkeypatch.setenv("ABX_LLM_API_KEY", "synthetic-secret")
    assert document._process([sys.executable, "-c", "import os;print('ABX_LLM_API_KEY' in os.environ)"], cwd=str(workspace), timeout=2) == b"False\n"
