"""Owned non-privileged OSWorld desktop slice, without a VM control plane."""
from __future__ import annotations

import atexit
import json
import os
from pathlib import Path
import select
import shutil
import signal
import subprocess
import tempfile
import threading
import time

from agent_sandbox.server import command, start

UPSTREAM_COMMIT = "b138d348256078fa634fc3b73567a7337c793e6b"
_LOCK = threading.RLock()
_PROCESS: subprocess.Popen | None = None
_STATE: tempfile.TemporaryDirectory | None = None
_BUFFER = b""


def _root() -> Path:
    return Path(os.environ.get("WORKSPACE", "/home/user/app")).resolve(strict=True)


def _task_path(path: str) -> str:
    target = Path(path)
    if not target.is_absolute():
        target = _root() / target
    try:
        target = target.resolve(strict=True)
    except OSError:
        raise ValueError("task_path must name an existing file inside WORKSPACE") from None
    if not target.is_relative_to(_root()) or not target.is_file():
        raise ValueError("task_path must be a file inside WORKSPACE")
    if target.stat().st_size > 65536:
        raise ValueError("task configuration exceeds 64 KiB")
    return str(target)


def _running() -> bool:
    with _LOCK:
        process = _PROCESS
        return process is not None and process.returncode is None and os.waitid(
            os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is None


def _members(group: int) -> bool:
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            fields = (entry / "stat").read_text().rsplit(")", 1)[1].split()
            if int(fields[2]) == group and fields[0] != "Z":
                return True
        except (OSError, ValueError, IndexError):
            pass
    return False


def _stop() -> None:
    global _PROCESS, _STATE, _BUFFER
    process = _PROCESS
    if process is not None and process.returncode is None:
        # Keep the leader unreaped as the PGID identity anchor, including after
        # unexpected exit. Never signal a PID loaded from a file or inspect poll().
        try:
            os.killpg(process.pid, signal.SIGTERM)
            deadline = time.monotonic() + 1
            while _members(process.pid) and time.monotonic() < deadline:
                time.sleep(.02)
            os.killpg(process.pid, signal.SIGKILL)
            deadline = time.monotonic() + 2
            while _members(process.pid) and time.monotonic() < deadline:
                time.sleep(.02)
            if _members(process.pid):
                raise RuntimeError("owned desktop process group cleanup timed out")
        except ProcessLookupError:
            pass
        process.wait(timeout=5)
    if process is not None:
        for stream in (process.stdin, process.stdout):
            if stream is not None:
                stream.close()
    _PROCESS = None
    _BUFFER = b""
    if _STATE is not None:
        _STATE.cleanup()
        _STATE = None


def _response(timeout: int) -> object:
    global _BUFFER
    deadline = time.monotonic() + timeout
    try:
        while b"\n" not in _BUFFER:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError("desktop operation timed out")
            if not select.select([_PROCESS.stdout], [], [], remaining)[0]:
                raise RuntimeError("desktop operation timed out")
            chunk = os.read(_PROCESS.stdout.fileno(), 65536)
            if not chunk:
                raise RuntimeError("desktop worker exited unexpectedly")
            _BUFFER += chunk
            if len(_BUFFER) > 8 * 1024 * 1024:
                raise RuntimeError("desktop response exceeds 8 MiB")
        line, _BUFFER = _BUFFER.split(b"\n", 1)
        result = json.loads(line)
        if result.get("error"):
            raise RuntimeError(result["error"])
        return result["result"]
    except (OSError, ValueError, KeyError, TypeError):
        _stop()
        raise RuntimeError("invalid desktop worker response") from None
    except BaseException:
        _stop()
        raise


def _request(operation: str, timeout: int = 30, **args):
    with _LOCK:
        if not _running():
            _stop()
            raise RuntimeError("desktop is not running; call desktop_start first")
        payload = (json.dumps({"operation": operation, **args}, ensure_ascii=False) + "\n").encode()
        if len(payload) > 32768:
            raise ValueError("desktop request exceeds 32 KiB")
        try:
            # A stalled worker must not block a request while writing to a full
            # pipe (Linux pipe capacity may be smaller than the request limit).
            descriptor = _PROCESS.stdin.fileno()
            os.set_blocking(descriptor, False)
            deadline = time.monotonic() + timeout
            pending = memoryview(payload)
            while pending:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not select.select([], [descriptor], [], remaining)[1]:
                    _stop()
                    raise RuntimeError("desktop request write timed out")
                try:
                    pending = pending[os.write(descriptor, pending):]
                except BlockingIOError:
                    continue
        except (OSError, ValueError):
            _stop()
            raise RuntimeError("desktop worker exited unexpectedly") from None
        except BaseException:
            _stop()
            raise
        return _response(timeout)


@command("osworld_setup_check", description="Report the pinned source and available desktop dependencies without starting a session.")
def osworld_setup_check() -> dict:
    return {"upstream_commit": UPSTREAM_COMMIT, "slice": "linux-browser",
            "dependencies": {name: bool(shutil.which(name)) for name in
                             ("Xvfb", "openbox", "xauth", "dbus-daemon", "xclip")},
            "running": _running(), "full_benchmark": False}


@command("desktop_start", description="Start one private Xvfb/Openbox/DBus/Chromium session owned by this server.")
def desktop_start() -> dict:
    global _PROCESS, _STATE
    with _LOCK:
        if _running():
            return {"running": True, "reused": True}
        _stop()
        for name in ("Xvfb", "openbox", "xauth", "dbus-daemon", "xclip"):
            if not shutil.which(name):
                raise RuntimeError(f"required desktop dependency is missing: {name}")
        _STATE = tempfile.TemporaryDirectory(prefix="abx-osworld-")
        # Preserve HOME. Isolate desktop configuration/profile with XDG paths
        # and explicit Xauthority/user-data-dir; disable Python user-site.
        # No cloud/model credentials or inherited DISPLAY enter the worker.
        env = {name: os.environ[name] for name in (
            "HOME", "PATH", "LANG", "LC_ALL", "LD_LIBRARY_PATH", "GI_TYPELIB_PATH",
            "PYTHONPATH", "XDG_DATA_DIRS", "IMLIB2_LOADER_PATH", "OSWORLD_BROWSER",
            "PLAYWRIGHT_BROWSERS_PATH") if name in os.environ}
        env.update({"XDG_CONFIG_HOME": _STATE.name + "/config",
                    "XDG_CACHE_HOME": _STATE.name + "/cache", "XDG_RUNTIME_DIR": _STATE.name,
                    "XDG_SESSION_TYPE": "x11", "WORKSPACE": str(_root()),
                    "NO_AT_BRIDGE": "0", "ACCESSIBILITY_ENABLED": "1",
                    "PYTHONNOUSERSITE": "1", "PYTHONUNBUFFERED": "1"})
        executable = os.environ.get("OSWORLD_RUNTIME_PYTHON", "/opt/osworld/bin/python")
        try:
            _PROCESS = subprocess.Popen([executable, str(Path(__file__).with_name("runtime.py")), _STATE.name],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                env=env, cwd=str(_root()), start_new_session=True)
            return _response(60)
        except OSError:
            _stop()
            raise RuntimeError("desktop worker could not start; check the runtime installation") from None
        except BaseException:
            _stop()
            raise


@command("desktop_stop", description="Stop the owned desktop process group and remove its private profile and state.")
def desktop_stop() -> str:
    with _LOCK:
        _stop()
        return "stopped"


@command("screenshot", description="Capture the real desktop through the pinned OSWorld screenshot handler; return PNG base64.")
def screenshot() -> dict:
    return _request("screenshot")


@command("click", description="Send a real bounded PyAutoGUI mouse click to the desktop.")
def click(x: int, y: int, button: str = "left") -> str:
    if type(x) is not int or type(y) is not int or not (0 <= x < 1024 and 0 <= y < 768):
        raise ValueError("coordinates must be integers inside 1024x768")
    if button not in ("left", "middle", "right"):
        raise ValueError("button must be left, middle or right")
    return _request("click", x=x, y=y, button=button)


@command("type", description="Paste up to 4096 Unicode characters through private X11 clipboard and actual Ctrl+V events; then clear owned clipboard state.")
def type_text(text: str) -> str:
    if not isinstance(text, str) or not text or len(text) > 4096 or "\x00" in text:
        raise ValueError("text must contain 1..4096 Unicode characters without NUL")
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        raise ValueError("text must be valid UTF-8 Unicode") from None
    return _request("type_text", timeout=60, text=text)


@command("hotkey", description="Send 1..4 comma-separated PyAutoGUI key names; no shell or Python code.")
def hotkey(keys: str) -> str:
    if not isinstance(keys, str) or not 1 <= len(keys) <= 128:
        raise ValueError("keys must be a comma-separated string of 1..4 key names")
    parsed = keys.split(",")
    if not 1 <= len(parsed) <= 4 or any(not k or not k.isascii() or not k.replace("_", "").isalnum() for k in parsed):
        raise ValueError("invalid key names")
    return _request("hotkey", keys=parsed)


@command("a11y_tree", description="Read the real Linux AT-SPI accessibility tree through the pinned OSWorld handler.")
def a11y_tree() -> str:
    return _request("a11y_tree")


@command("run_task_config", description="Apply the supported OSWorld chrome_open_tabs/sleep task setup subset; reject unsupported operations.")
def run_task_config(task_path: str) -> dict:
    return _request("run_task_config", task_path=_task_path(task_path))


@command("evaluate", description="Evaluate real accessibility_tree using pinned OSWorld check_include_exclude/exact_match and rule expectations.")
def evaluate(task_path: str) -> dict:
    return _request("evaluate", task_path=_task_path(task_path))


@command("osworld_desktop_smoke", description="Run a real offline desktop task with screenshot, AT-SPI, GUI input and upstream evaluation, then clean up.")
def osworld_desktop_smoke() -> str:
    with _LOCK:
        if _running():
            raise RuntimeError("stop the existing desktop before running the disposable smoke")
        try:
            desktop_start()
            return _request("smoke", timeout=60)
        finally:
            _stop()


atexit.register(_stop)

if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
