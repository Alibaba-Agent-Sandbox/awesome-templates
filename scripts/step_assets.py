"""Bounded parallel transport for exact public build archives; stdlib only.

The generated build recipe copies this module into a temporary root-only cache.
Original installers still check their own digests, versions and extraction rules.
The cache and process-local URL adapter are removed before the runtime USER.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import platform
import re
import runpy
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

CHUNK = 1024 * 1024
MAX_BYTES = 300 * 1024 * 1024


def download(asset: dict, target: Path, *, workers: int = 16, seconds: int = 1200) -> None:
    """Require exact ranges/size and final SHA256 before atomic publication."""
    if not 1 <= workers <= 32 or not 1 <= seconds <= 1200:
        raise ValueError("invalid download concurrency/deadline")
    expected = asset["sha256"]
    if not re.fullmatch(r"[a-f0-9]{64}", expected):
        raise ValueError("immutable archive SHA256 is required")
    if target.exists():
        raise FileExistsError("asset cache destination already exists")
    deadline = time.monotonic() + seconds
    url = asset.get("transport_url", asset["url"])
    request = urllib.request.Request(url, headers={"Range": "bytes=0-0", "Accept-Encoding": "identity"})
    with urllib.request.urlopen(request, timeout=min(90, seconds)) as response:
        match = re.fullmatch(r"bytes 0-0/([0-9]+)", response.headers.get("Content-Range", ""))
        if response.status != 206 or not match or len(response.read(2)) != 1:
            raise RuntimeError("official archive does not provide exact byte ranges")
        size = int(match[1])
        # Reuse the official redirect target in memory. Repeating GitHub's
        # release redirect for every range adds TLS/redirect throttling; signed
        # CDN URLs never enter provenance, files or successful output.
        resolved_url = response.geturl()
    pinned_size = asset.get("size", asset.get("bytes"))
    if not 0 < size <= MAX_BYTES or pinned_size is not None and size != pinned_size:
        raise RuntimeError("official archive size differs from the bounded reviewed asset")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="parts-", dir=target.parent) as private:
        directory = Path(private)

        def fetch(index):
            start = index * CHUNK
            stop = min(size, start + CHUNK) - 1
            for attempt in range(4):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("parallel archive deadline exceeded")
                request = urllib.request.Request(resolved_url, headers={
                    "Range": f"bytes={start}-{stop}", "Accept-Encoding": "identity"})
                try:
                    with urllib.request.urlopen(request, timeout=min(90, remaining)) as response:
                        if response.status != 206 or response.headers.get("Content-Range") != f"bytes {start}-{stop}/{size}":
                            raise RuntimeError("official archive range does not match the requested bytes")
                        content = response.read(stop - start + 2)
                    if len(content) != stop - start + 1:
                        raise RuntimeError("truncated or oversized official archive range")
                    (directory / str(index)).write_bytes(content)
                    return index
                except (urllib.error.URLError, TimeoutError):
                    if attempt == 3:
                        raise
                    time.sleep(min(2 ** attempt, max(0, deadline - time.monotonic())))

        count = (size + CHUNK - 1) // CHUNK
        with ThreadPoolExecutor(max_workers=workers) as pool:
            list(pool.map(fetch, range(count)))
        digest = hashlib.sha256()
        complete = directory / "complete"
        with complete.open("xb") as output:
            for index in range(count):
                content = (directory / str(index)).read_bytes()
                digest.update(content)
                output.write(content)
        if digest.hexdigest() != expected:
            raise RuntimeError("official archive SHA256 mismatch")
        if time.monotonic() > deadline:
            raise TimeoutError("parallel archive deadline exceeded")
        complete.rename(target)


def main() -> None:
    root = Path(__file__).resolve().parent
    assets = json.loads((root / "assets.json").read_text())[platform.machine()]
    if sys.argv[1] == "fetch":
        item = assets[int(sys.argv[2])]
        target = root / item["sha256"]
        download(item, target)
        if item.get("mirror_path"):
            relative = Path(item["mirror_path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("invalid local Python mirror path")
            mirror = root / "python-mirror" / relative
            mirror.parent.mkdir(parents=True, exist_ok=True)
            os.link(target, mirror)
        if item.get("filename"):
            filename = Path(item["filename"])
            if filename.name != str(filename) or filename.suffix != ".whl":
                raise ValueError("invalid cached wheel filename")
            os.link(target, root / filename)
        print("PASS exact official build archive; parallel ranges and SHA256 verified", flush=True)
        return
    if sys.argv[1] == "install-uv":
        wheels = [item for item in assets if item.get("filename", "").startswith("uv-0.12.3-")]
        if len(wheels) != 1:
            raise ValueError("one exact UV bootstrap wheel is required")
        wheel = root / wheels[0]["filename"]
        with wheel.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != wheels[0]["sha256"]:
                raise RuntimeError("UV bootstrap wheel integrity mismatch")
        installer = "/tmp/abx-step-installer"
        subprocess.run([sys.executable, "-m", "venv", installer], check=True, timeout=120)
        subprocess.run([installer + "/bin/pip", "install", "--no-index", "--no-deps", str(wheel)], check=True, timeout=120)
        version = subprocess.check_output([installer + "/bin/uv", "--version"], text=True, timeout=15)
        if not version.startswith("uv 0.12.3"):
            raise RuntimeError("UV bootstrap version mismatch")
        return
    if sys.argv[1] == "playwright":
        files = {}
        for item in assets:
            if "playwright_path" not in item:
                continue
            path = root / item["sha256"]
            with path.open("rb") as stream:
                if hashlib.file_digest(stream, "sha256").hexdigest() != item["sha256"]:
                    raise RuntimeError("Playwright archive cache integrity mismatch")
            files["/" + item["playwright_path"]] = path
        if not files:
            raise ValueError("fixed Playwright browser cache is missing")

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                path = files.get(self.path)
                if path is None:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Length", str(path.stat().st_size))
                self.end_headers()
                with path.open("rb") as stream:
                    while block := stream.read(1024 * 1024):
                        self.wfile.write(block)

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        env = dict(os.environ, PLAYWRIGHT_DOWNLOAD_HOST=f"http://127.0.0.1:{server.server_port}")
        for name in ("PLAYWRIGHT_CHROMIUM_DOWNLOAD_HOST", "PLAYWRIGHT_FIREFOX_DOWNLOAD_HOST", "PLAYWRIGHT_WEBKIT_DOWNLOAD_HOST"):
            env.pop(name, None)
        try:
            result = subprocess.run(sys.argv[2:], env=env, timeout=900)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
        raise SystemExit(result.returncode)
    if sys.argv[1] != "run":
        raise ValueError("unsupported build asset operation")
    original = urllib.request.urlopen
    cached = {item["url"]: root / item["sha256"] for item in assets}

    def urlopen(url, *args, **kwargs):
        name = url.full_url if isinstance(url, urllib.request.Request) else url
        if name in cached:
            path = cached[name]
            # An installer may not consume an unverified, absent or changed cache.
            with path.open("rb") as stream:
                if hashlib.file_digest(stream, "sha256").hexdigest() != path.name:
                    raise RuntimeError("build asset cache integrity mismatch")
            return original(path.as_uri(), *args, **kwargs)
        return original(url, *args, **kwargs)

    urllib.request.urlopen = urlopen
    sys.argv = sys.argv[2:]
    if sys.argv[0] == "-":
        exec(compile(sys.stdin.read(), "<stdin>", "exec"), {"__name__": "__main__"})
    else:
        runpy.run_path(sys.argv[0], run_name="__main__")


if __name__ == "__main__":
    main()
