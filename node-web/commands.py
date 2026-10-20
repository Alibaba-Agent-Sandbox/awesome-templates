"""Manage one real Node HTTP service per sandbox, with bounded buffered logs."""
from __future__ import annotations

import atexit
import http.client
import os
from pathlib import Path
import signal
import socket
import subprocess
import tempfile
import threading
import time

from agent_sandbox.server import command, start

_LOCK = threading.RLock()
_LOG_LOCK = threading.Lock()
_STATE: dict = {}
_LOG_DIR = Path(tempfile.mkdtemp(prefix="node-web-logs-"))
_LOG = _LOG_DIR / "service.log"
_LOG_LIMIT = 1024 * 1024


def _workdir(cwd: str) -> Path:
    directory = Path(cwd or os.environ.get("WORKSPACE") or "/home/user/app")
    if not cwd and not directory.is_dir():
        directory = Path.cwd()
    if not directory.is_dir():
        raise ValueError("cwd must be an existing application directory")
    return directory.resolve()


def _range(value: int, low: int, high: int, name: str) -> None:
    if not low <= value <= high:
        raise ValueError(f"{name} must be between {low} and {high}")


def _drain(stream) -> None:
    """Continuously consume child output; at most two 1 MiB log files remain."""
    try:
        while data := stream.read1(8192):
            with _LOG_LOCK:
                if _LOG.exists() and _LOG.stat().st_size + len(data) > _LOG_LIMIT:
                    _LOG.replace(_LOG.with_suffix(".log.1"))
                with _LOG.open("ab") as output:
                    output.write(data)
    finally:
        stream.close()


def _http(port: int, path: str = "/", timeout: float = 1) -> dict:
    if not path.startswith("/") or path.startswith("//") or "\r" in path or "\n" in path:
        raise ValueError("path must be a local absolute HTTP path")
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        body = response.read(65537)
        return {"status_code": response.status, "body": body[:65536].decode("utf-8", "replace"),
                "truncated": len(body) > 65536}
    finally:
        connection.close()


def _terminate(proc: subprocess.Popen) -> None:
    if getattr(proc, "_node_web_group_stopped", False):
        return
    # The npm launcher may exit while its Node descendant remains alive. The
    # session/process-group id is stable, so signal the entire owned group.
    for sig, wait in ((signal.SIGTERM, 3), (signal.SIGKILL, 2)):
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            break
        try:
            proc.wait(timeout=wait)
        except subprocess.TimeoutExpired:
            continue
        # Even if the group leader exited, reap/kill remaining descendants.
        if sig == signal.SIGTERM:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        break
    proc.wait(timeout=2)
    proc._node_web_group_stopped = True
    thread = _STATE.get("reader") if _STATE.get("process") is proc else None
    if thread:
        thread.join(timeout=2)


def _launch(argv: list[str], cwd: str, port: int, ready_path: str, timeout_s: int) -> dict:
    _range(port, 1024, 65535, "port")
    if port == int(os.environ.get("ABX_SERVER_PORT", "9000")):
        raise ValueError("port is reserved for the command server")
    _range(timeout_s, 1, 120, "timeout_s")
    # Validate before creating a process.
    if not ready_path.startswith("/") or ready_path.startswith("//") or any(c in ready_path for c in "\r\n"):
        raise ValueError("ready_path must be a local absolute HTTP path")
    directory = _workdir(cwd)
    with _LOCK:
        previous = _STATE.get("process")
        if previous is not None and previous.poll() is None:
            raise RuntimeError("a service is already running; call stop first")
        if previous is not None:
            _terminate(previous)
        # Avoid claiming an unrelated HTTP listener as our successful startup.
        with socket.socket() as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(("0.0.0.0", port))
            except OSError as exc:
                raise RuntimeError("requested port is already in use") from exc
        with _LOG_LOCK:
            _LOG.unlink(missing_ok=True)
            _LOG.with_suffix(".log.1").unlink(missing_ok=True)
        env = {**os.environ, "PORT": str(port), "HOST": "0.0.0.0"}
        proc = subprocess.Popen(argv, cwd=directory, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, start_new_session=True)
        reader = threading.Thread(target=_drain, args=(proc.stdout,), daemon=True)
        _STATE.update(process=proc, reader=reader, port=port, cwd=str(directory), argv=argv,
                      ready_path=ready_path)
        reader.start()
        deadline = time.monotonic() + timeout_s
        try:
            while time.monotonic() < deadline:
                if proc.poll() is not None:
                    raise RuntimeError(f"service exited before HTTP readiness (exit {proc.returncode}); inspect logs")
                try:
                    response = _http(port, ready_path, timeout=min(1, max(.05, deadline - time.monotonic())))
                    if 200 <= response["status_code"] < 400 and proc.poll() is None:
                        return {"pid": proc.pid, "port": port, "status": "running", "cwd": str(directory),
                                "http_status": response["status_code"]}
                except (OSError, http.client.HTTPException):
                    pass
                time.sleep(.05)
            raise RuntimeError("service did not return HTTP 2xx/3xx before timeout_s; inspect logs")
        except Exception:
            _terminate(proc)
            raise


@command("serve", description="Start node <entry> and require an HTTP readiness response.")
def serve(entry: str = "index.js", port: int = 3000, cwd: str = "", ready_path: str = "/", timeout_s: int = 20) -> dict:
    directory = _workdir(cwd)
    path = (directory / entry).resolve()
    if not path.is_file():
        raise ValueError("entry must name an existing JavaScript file")
    return _launch(["node", str(path)], str(directory), port, ready_path, timeout_s)


@command("start", description="Start npm start in the background and require HTTP readiness.")
def start_service(port: int = 3000, cwd: str = "", ready_path: str = "/", timeout_s: int = 20) -> dict:
    return _launch(["npm", "start"], cwd, port, ready_path, timeout_s)


@command("dev", description="Start npm run dev in the background and require HTTP readiness.")
def dev(port: int = 3000, cwd: str = "", ready_path: str = "/", timeout_s: int = 20) -> dict:
    return _launch(["npm", "run", "dev"], cwd, port, ready_path, timeout_s)


@command("status", description="Return process liveness and an actual HTTP readiness probe.")
def status() -> dict:
    with _LOCK:
        proc = _STATE.get("process")
        if proc is None:
            return {"status": "stopped", "pid": None, "http_ready": False}
        running = proc.poll() is None
        code = None
        if running:
            try:
                code = _http(_STATE["port"], _STATE["ready_path"])["status_code"]
            except (OSError, http.client.HTTPException):
                pass
        return {"status": "running" if running else "stopped", "pid": proc.pid,
                "port": _STATE["port"], "exit_code": proc.returncode,
                "http_ready": code is not None and 200 <= code < 400, "http_status": code}


@command("stop", description="Stop the owned service process group, including npm children.")
def stop() -> dict:
    with _LOCK:
        proc = _STATE.get("process")
        if proc is not None:
            _terminate(proc)
        return {"status": "stopped", "pid": proc.pid if proc else None}


@command("logs", description="Read the newest bounded service stdout/stderr bytes.")
def logs(max_bytes: int = 16384) -> dict:
    _range(max_bytes, 1, 131072, "max_bytes")
    with _LOG_LOCK:
        data = b""
        for path in (_LOG.with_suffix(".log.1"), _LOG):
            if path.exists():
                with path.open("rb") as stream:
                    stream.seek(max(0, path.stat().st_size - max_bytes))
                    data = (data + stream.read(max_bytes))[-max_bytes:]
        return {"output": data.decode("utf-8", "replace"), "max_bytes": max_bytes}


@command("request", description="GET a local service path and return status plus up to 64 KiB of body.")
def request(path: str = "/", timeout_s: int = 5) -> dict:
    _range(timeout_s, 1, 30, "timeout_s")
    with _LOCK:
        proc = _STATE.get("process")
        if proc is None or proc.poll() is not None:
            raise RuntimeError("no service is running")
        try:
            return _http(_STATE["port"], path, timeout_s)
        except (OSError, http.client.HTTPException) as exc:
            raise RuntimeError("service HTTP request failed") from exc


@command("build", description="Run npm run build with an execution deadline and bounded output.")
def build(cwd: str = "", timeout_s: int = 120) -> dict:
    _range(timeout_s, 1, 600, "timeout_s")
    # A temporary regular file keeps verbose builds from filling a PIPE or RAM.
    with tempfile.TemporaryFile() as output:
        proc = subprocess.Popen(["npm", "run", "build"], cwd=_workdir(cwd),
                                stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            proc.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired as exc:
            _terminate(proc)
            raise RuntimeError("build exceeded timeout_s") from exc
        output.seek(0, os.SEEK_END)
        size = output.tell()
        output.seek(max(0, size - 131072))
        text = output.read().decode("utf-8", "replace")
        if proc.returncode:
            raise RuntimeError(f"build failed (exit {proc.returncode}); inspect the application build locally")
        return {"exit_code": 0, "output": text, "truncated": size > 131072}


@command("smoke", description="Start the bundled sample, assert a real HTTP response, and stop it.")
def smoke() -> str:
    with _LOCK:
        serve(entry=str(Path(__file__).with_name("index.js")), port=3000)
        try:
            response = request()
            if response["status_code"] != 200 or response["body"] != "node-web ready\n":
                raise RuntimeError("sample HTTP response did not match")
            return "node-web ready"
        finally:
            stop()


atexit.register(stop)

if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
