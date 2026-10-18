"""Pinned Gemini headless commands with explicit tool approval and bounded execution."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import threading
import time

from agent_sandbox.server import command, start

PINNED_VERSION = "0.64.0"
DEFAULT_MODEL = "gemini-3.1-flash-lite"


def _redact(text: str) -> str:
    values = {value for name, value in os.environ.items() if value and any(
        part in name.upper() for part in ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL"))}
    for value in sorted(values, key=len, reverse=True):
        text = text.replace(json.dumps(value)[1:-1], "[REDACTED]").replace(value, "[REDACTED]")
    return text


def _workdir(cwd: str = "") -> str:
    root = Path(os.environ.get("WORKSPACE") or "/home/user/app").resolve()
    if not root.is_dir():
        raise ValueError("WORKSPACE must name an existing directory")
    candidate = Path(cwd) if cwd else root
    path = (candidate if candidate.is_absolute() else root / candidate).resolve()
    if not path.is_relative_to(root):
        raise ValueError("cwd must stay inside WORKSPACE")
    if not path.is_dir():
        raise ValueError("cwd must name an existing directory")
    return str(path)


def _executable() -> str:
    path = shutil.which("gemini")
    if not path:
        raise RuntimeError("gemini CLI is missing; install @google/gemini-cli@0.64.0")
    return path


def _run_process(argv: list[str], *, cwd: str, timeout: int | float,
                 env: dict | None = None, input_text: str | None = None) -> tuple[int, str, str]:
    """Keep the Linux session leader unreaped until its owned group is stopped."""
    process = subprocess.Popen(argv, cwd=cwd, env=env,
        stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    stdout_parts: list[bytes] = []
    stderr_parts: list[bytes] = []
    def drain(stream, parts):
        try:
            while chunk := stream.read(65536):
                parts.append(chunk)
        except OSError:
            pass
        finally:
            stream.close()
    readers = [threading.Thread(target=drain, args=(process.stdout, stdout_parts), daemon=True),
               threading.Thread(target=drain, args=(process.stderr, stderr_parts), daemon=True)]
    for reader in readers:
        reader.start()
    if input_text is not None:
        def feed():
            try:
                process.stdin.write(input_text.encode())
                process.stdin.close()
            except (OSError, ValueError):
                pass
            finally:
                try:
                    process.stdin.close()
                except (OSError, ValueError):
                    pass
        threading.Thread(target=feed, daemon=True).start()
    deadline = time.monotonic() + timeout
    timed_out = False
    try:
        while os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is None:
            if time.monotonic() >= deadline:
                timed_out = True
                break
            time.sleep(0.02)
    finally:
        # WNOWAIT pins the original PID/PGID even after leader exit. No poll(),
        # wait() or communicate() may reap it before group cleanup.
        if timed_out:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            grace = time.monotonic() + 1
            while time.monotonic() < grace:
                if os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None:
                    break
                time.sleep(0.02)
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            raise RuntimeError("owned process cleanup timed out") from None
        for reader in readers:
            reader.join(timeout=2)
    if timed_out:
        raise RuntimeError(f"gemini timed out after {timeout} seconds") from None
    return (process.returncode, b"".join(stdout_parts).decode("utf-8", "replace"),
            b"".join(stderr_parts).decode("utf-8", "replace"))


def _run(argv: list[str], *, command_timeout: int, cwd: str = "") -> str:
    try:
        code, stdout, stderr = _run_process(argv, cwd=_workdir(cwd), timeout=command_timeout)
    except OSError:
        raise RuntimeError("gemini process could not start") from None
    if code:
        raise RuntimeError(_redact(stderr or stdout).strip() or f"gemini exited {code}")
    return _redact(stdout)


@command("gemini_version", description="Read the installed gemini --version without model authentication.")
def gemini_version() -> str:
    return _run([_executable(), "--version"], command_timeout=30).strip()


@command("gemini_setup_check", description="Inspect installation, key presence and settings without changing configuration.")
def gemini_setup_check() -> dict:
    settings = []
    for path in (Path.home() / ".gemini" / "settings.json", Path(_workdir()) / ".gemini" / "settings.json"):
        valid = True
        if path.exists():
            try:
                valid = isinstance(json.loads(path.read_text(encoding="utf-8")), dict)
            except (OSError, ValueError):
                valid = False
        settings.append({"path": str(path), "exists": path.exists(), "valid_json_object": valid})
    installed = shutil.which("gemini") is not None
    return {"installed": installed, "version": gemini_version() if installed else "",
            "pinned_version": PINNED_VERSION,
            "api_key_set": bool(os.environ.get("GEMINI_API_KEY", "").strip()),
            "model_set": bool(os.environ.get("GEMINI_MODEL", "").strip()),
            "workspace": _workdir(), "settings": settings}


@command("gemini", description="Run Gemini headlessly; tool editing requires explicit yolo approval.")
def gemini(prompt: str, model: str = "", cwd: str = "",
           command_timeout: int = 600, yolo: bool = False) -> str:
    if not prompt.strip():
        raise ValueError("prompt must not be empty")
    if not 1 <= command_timeout <= 1800:
        raise ValueError("command_timeout must be between 1 and 1800 seconds")
    _workdir(cwd)
    if not os.environ.get("GEMINI_API_KEY", "").strip():
        raise RuntimeError("GEMINI_API_KEY is required; interactive OAuth login is disabled")
    chosen = (model or os.environ.get("GEMINI_MODEL") or DEFAULT_MODEL).strip() or DEFAULT_MODEL
    argv = [_executable(), "-p", prompt, "--model", chosen, "--output-format", "json"]
    # Read-only plan is the default. Headless execution never waits for stdin approval.
    argv.extend(["--approval-mode", "yolo" if yolo else "plan"])
    return _run(argv, command_timeout=command_timeout, cwd=cwd)


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
