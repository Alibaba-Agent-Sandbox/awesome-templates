"""Exercise actual ranged HTTP, integrity failures and process-local caching."""
from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import threading

import pytest

import step_assets
from prepare_steps import ROOT, prepare


@contextmanager
def server(content, *, malformed=False):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            start, end = map(int, self.headers["Range"].removeprefix("bytes=").split("-"))
            self.send_response(206)
            self.send_header("Content-Range", "invalid" if malformed else f"bytes {start}-{end}/{len(content)}")
            self.end_headers()
            self.wfile.write(content[start:end + 1])

        def log_message(self, *args):
            pass

    http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{http.server_port}/archive"
    finally:
        http.shutdown()
        http.server_close()
        thread.join()


def test_actual_ranges_reconstruct_exact_bytes(tmp_path):
    content = bytes(range(256)) * 4097
    target = tmp_path / "archive"
    with server(content) as url:
        step_assets.download({"url": url, "sha256": hashlib.sha256(content).hexdigest(), "size": len(content)}, target, workers=3)
    assert target.read_bytes() == content


@pytest.mark.parametrize("failure", ["range", "size", "digest"])
def test_invalid_archive_cannot_be_published(tmp_path, failure):
    content = b"archive" * 100
    target = tmp_path / "archive"
    with server(content, malformed=failure == "range") as url:
        asset = {"url": url, "sha256": "0" * 64 if failure == "digest" else hashlib.sha256(content).hexdigest(),
                 "size": len(content) + (1 if failure == "size" else 0)}
        with pytest.raises(RuntimeError):
            step_assets.download(asset, target)
    assert not target.exists()
    assert not list(tmp_path.glob("parts-*"))


def test_installer_consumes_only_exact_verified_cache(tmp_path):
    content = b"immutable-official-archive"
    digest = hashlib.sha256(content).hexdigest()
    (tmp_path / digest).write_bytes(content)
    (tmp_path / "assets.json").write_text(json.dumps({platform.machine(): [{"url": "https://official.invalid/archive", "sha256": digest}]}))
    helper = tmp_path / "step_assets.py"
    shutil.copy2(Path(step_assets.__file__), helper)
    script = tmp_path / "installer.py"
    script.write_text("import urllib.request\nwith urllib.request.urlopen('https://official.invalid/archive') as f: print(f.read().decode())\n")
    command = [sys.executable, str(helper), "run", str(script)]
    assert subprocess.check_output(command, text=True).strip() == content.decode()
    (tmp_path / digest).write_bytes(b"tampered")
    result = subprocess.run(command, text=True, capture_output=True)
    assert result.returncode != 0 and "cache integrity mismatch" in result.stderr
    assert script.read_text().startswith("import urllib.request")


@pytest.mark.parametrize("name", ["goose", "crush", "code-server", "polyglot-toolchain", "aider", "swe", "hermes-agent"])
def test_generated_cache_preserves_original_source_and_is_removed_before_runtime(name):
    manifest, proof = prepare(ROOT / name, asset_transport="parallel", server_commit="e2cb27e24fde0a67112f82b8d44af463445a5d1a")
    steps = manifest["build"]["steps"]
    assert proof["asset_transport"] == "parallel"
    assert proof["steps_json_bytes"] <= 15000
    assert any("step_assets.py fetch 0" in step["args"][0] for step in steps if step["type"] == "RUN")
    if name not in {"hermes-agent", "aider"}:
        assert any("step_assets.py run" in step["args"][0] for step in steps if step["type"] == "RUN")
    if name == "hermes-agent":
        assert proof["python_download_profile"].startswith("uv0.12.3")
        assert any("uv python install cpython-3.14.6-linux-$(uname -m)-gnu" in step["args"][0] for step in steps if step["type"] == "RUN")
    assert steps[-1] == {"type": "USER", "args": ["user"]}
    # compact_run retains short cleanup commands in plaintext.
    assert "rm -rf /tmp/abx-step-assets" in steps[-2]["args"][0]


@pytest.mark.parametrize("name", ["deepagents", "osworld"])
def test_parallel_locked_installer_retains_hashes_and_removes_build_tool(name):
    manifest, proof = prepare(ROOT / name, asset_transport="parallel", server_commit="e2cb27e24fde0a67112f82b8d44af463445a5d1a")
    commands = [step["args"][0] for step in manifest["build"]["steps"] if step["type"] == "RUN"]
    locked = [command for command in commands if "uv --no-cache pip install" in command]
    assert len(locked) == 1 and "--require-hashes" in locked[0]
    assert "uv0.12.3" in proof["python_package_transport"]
    assert manifest["build"]["steps"][-2]["args"][0].startswith("rm -rf ")
    assert "/tmp/abx-step-installer" in manifest["build"]["steps"][-2]["args"][0]
    assert proof["steps_json_bytes"] <= 15000


@pytest.mark.parametrize("requested,exit_code", [("/fixed/browser.zip", 0), ("/assets.json", 1)])
def test_loopback_browser_mirror_serves_only_verified_archives(tmp_path, requested, exit_code):
    content = b"fixed official browser zip fixture"
    digest = hashlib.sha256(content).hexdigest()
    (tmp_path / digest).write_bytes(content)
    (tmp_path / "assets.json").write_text(json.dumps({platform.machine(): [
        {"url": "https://official.invalid/browser.zip", "sha256": digest, "playwright_path": "fixed/browser.zip"}]}))
    helper = tmp_path / "step_assets.py"
    shutil.copy2(Path(step_assets.__file__), helper)
    program = ("import os,urllib.request; "
               f"print(urllib.request.urlopen(os.environ['PLAYWRIGHT_DOWNLOAD_HOST']+{requested!r}).read().decode())")
    result = subprocess.run([sys.executable, str(helper), "playwright", sys.executable, "-c", program],
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == exit_code
    if exit_code == 0:
        assert result.stdout.strip() == content.decode()
