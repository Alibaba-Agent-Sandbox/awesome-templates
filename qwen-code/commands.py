"""Pinned Qwen Code headless commands; diagnostics never rewrite configuration."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import threading
import time

from agent_sandbox.server import command, start

PINNED_VERSION = "0.23.0"


def _redact(text: str) -> str:
    values = {value for name, value in os.environ.items() if value and any(
        part in name.upper() for part in ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL"))}
    for value in sorted(values, key=len, reverse=True):
        text = text.replace(json.dumps(value)[1:-1], "[REDACTED]").replace(value, "[REDACTED]")
    return text


def _api_key() -> str:
    return next((value for name in ("OPENAI_API_KEY", "DASHSCOPE_API_KEY")
                 if (value := os.environ.get(name, "")).strip()), "")


def _workdir(cwd: str = "") -> str:
    root = Path(os.environ.get("WORKSPACE") or "/home/user/app")
    if not root.is_dir():
        root = Path.cwd()
    path = Path(cwd) if cwd else root
    if not path.is_absolute():
        path = root / path
    if not path.is_dir():
        raise ValueError("cwd must name an existing directory")
    return str(path.resolve())


def _executable() -> str:
    path = shutil.which("qwen")
    if not path:
        raise RuntimeError("qwen CLI is missing; install @qwen-code/qwen-code@0.23.0")
    return path


# Generated from scripts/process_runners/text.py; update with scripts/sync_process_runners.py.
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
        raise RuntimeError(f"command timed out after {timeout} seconds") from None
    return (process.returncode, b"".join(stdout_parts).decode("utf-8", "replace"),
            b"".join(stderr_parts).decode("utf-8", "replace"))


def _run(argv: list[str], *, timeout: int, cwd: str = "", env: dict | None = None) -> str:
    code, stdout, stderr = _run_process(argv, cwd=_workdir(cwd), timeout=timeout, env=env)
    if code:
        raise RuntimeError(_redact(stderr or stdout) or f"command exited {code}")
    return _redact(stdout)


@command("qwen_version", description="Read the installed qwen --version without model authentication.")
def qwen_version() -> str:
    return _run([_executable(), "--version"], timeout=30).strip()


@command("qwen_setup_check", description="Inspect installation, key presence and settings without changing files.")
def qwen_setup_check() -> dict:
    paths = [Path.home() / ".qwen" / "settings.json", Path(_workdir()) / ".qwen" / "settings.json"]
    settings = []
    for path in paths:
        valid = True
        if path.exists():
            try:
                valid = isinstance(json.loads(path.read_text(encoding="utf-8")), dict)
            except (OSError, ValueError):
                valid = False
        # Never return arbitrary configuration values, which may contain credentials.
        settings.append({"path": str(path), "exists": path.exists(), "valid_json_object": valid})
    installed = shutil.which("qwen") is not None
    return {
        "installed": installed, "version": qwen_version() if installed else "",
        "pinned_version": PINNED_VERSION,
        "api_key_set": bool(_api_key()),
        "auth_type": "openai", "model_set": bool(os.environ.get("OPENAI_MODEL", "").strip()),
        "base_url_set": bool(os.environ.get("OPENAI_BASE_URL", "").strip()),
        "settings": settings,
    }


@command("qwen", description="Run Qwen Code headlessly with OpenAI-compatible authentication.")
def qwen(prompt: str, max_turns: int = 100, model: str = "", cwd: str = "",
         command_timeout: int = 600, yolo: bool = False) -> str:
    """Return buffered JSON text. yolo explicitly approves all agent tool actions."""
    if not prompt.strip():
        raise ValueError("prompt must not be empty")
    if not 1 <= max_turns <= 1000:
        raise ValueError("max_turns must be between 1 and 1000")
    if not 1 <= command_timeout <= 1800:
        raise ValueError("command_timeout must be between 1 and 1800 seconds")
    env = os.environ.copy()
    env["OPENAI_API_KEY"] = _api_key()
    if not env["OPENAI_API_KEY"].strip():
        raise RuntimeError("OPENAI_API_KEY or DASHSCOPE_API_KEY is required; interactive OAuth login is disabled")
    args = [_executable(), "-p", prompt, "--auth-type", "openai", "--output-format", "json",
            "--max-session-turns", str(max_turns), "--max-wall-time", str(command_timeout),
            "--no-chat-recording"]
    if model:
        args.extend(["--model", model])
    if yolo:
        args.append("--yolo")
    return _run(args, timeout=command_timeout, cwd=cwd, env=env)


@command("run", description="Run a Python script in the workspace.")
def run(script: str = "main.py") -> str:
    return _run([sys.executable, script], timeout=120)


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
