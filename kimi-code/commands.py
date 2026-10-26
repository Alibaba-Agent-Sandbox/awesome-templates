"""Pinned Kimi Code headless CLI with per-request private runtime state."""
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
import tempfile

from agent_sandbox.server import command, start

PINNED_VERSION = "2.2.0"


def _redact(text: str) -> str:
    values = {value for name, value in os.environ.items() if value and any(
        part in name.upper() for part in ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL"))}
    for value in sorted(values, key=len, reverse=True):
        for variant in (json.dumps(value)[1:-1], json.dumps(value, ensure_ascii=False)[1:-1], value):
            text = text.replace(variant, "[REDACTED]")
    return text


def _workdir(cwd: str = "") -> str:
    root = Path(os.environ.get("WORKSPACE") or "/home/user/app")
    path = Path(cwd) if cwd else root
    if not path.is_absolute():
        path = root / path
    if not path.is_dir():
        raise ValueError("cwd must name an existing directory")
    return str(path.resolve())


def _executable() -> str:
    path = shutil.which("kimi")
    if not path:
        raise RuntimeError("Kimi Code CLI is missing; install @moonshot-ai/kimi-code@2.2.0")
    return path


# Generated from scripts/process_runners/bounded_text.py; update with scripts/sync_process_runners.py.
def _run_process(argv: list[str], *, cwd: str, timeout: int | float,
                 env: dict | None = None, input_text: str | None = None) -> tuple[int, str, str]:
    """Keep the Linux session leader unreaped until its owned group is stopped."""
    process = subprocess.Popen(argv, cwd=cwd, env=env,
        stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    stdout_parts: list[bytes] = []
    stderr_parts: list[bytes] = []
    overflow = threading.Event()
    def drain(stream, parts):
        size = 0
        try:
            while chunk := stream.read(65536):
                size += len(chunk)
                if size > 8 * 1024 * 1024:
                    overflow.set()
                else:
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
            if overflow.is_set():
                break
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
    if overflow.is_set():
        raise RuntimeError("command output exceeded the 8 MiB per-stream limit") from None
    if timed_out:
        raise RuntimeError(f"command timed out after {timeout} seconds") from None
    return (process.returncode, b"".join(stdout_parts).decode("utf-8", "replace"),
            b"".join(stderr_parts).decode("utf-8", "replace"))


def _run(argv: list[str], *, timeout: int, cwd: str = "", env: dict | None = None) -> str:
    code, stdout, stderr = _run_process(argv, cwd=_workdir(cwd), timeout=timeout, env=env)
    if code:
        raise RuntimeError(_redact(stderr or stdout) or f"command exited {code}")
    return _redact(stdout)


@command("kimi_version", description="Read the pinned Kimi Code CLI version without model credentials.")
def kimi_version() -> str:
    with tempfile.TemporaryDirectory(prefix="abx-kimi-inspect-") as state:
        env = os.environ.copy()
        env["KIMI_CODE_HOME"] = state
        return _run([_executable(), "--version"], timeout=30, env=env).strip()


@command("kimi_setup_check", description="Inspect Kimi installation and model environment without changing caller settings.")
def kimi_setup_check() -> dict:
    installed = shutil.which("kimi") is not None
    return {"installed": installed, "version": kimi_version() if installed else "",
            "pinned_version": PINNED_VERSION,
            "model_set": bool(os.environ.get("KIMI_MODEL_NAME", "").strip()),
            "key_set": bool(os.environ.get("KIMI_MODEL_API_KEY", "").strip()),
            "base_url_set": bool(os.environ.get("KIMI_MODEL_BASE_URL", "").strip()),
            "workspace": _workdir()}


@command("kimi", description="Run one bounded Kimi prompt with isolated settings; automatic tool permission is explicit.")
def kimi(prompt: str, cwd: str = "", command_timeout: int = 600, allow_tools: bool = False) -> str:
    if not prompt.strip() or len(prompt.encode()) > 65536:
        raise ValueError("prompt must contain 1..65536 UTF-8 bytes")
    if not 1 <= command_timeout <= 1800:
        raise ValueError("command_timeout must be 1..1800 seconds")
    if not all(os.environ.get(name, "").strip() for name in
               ("KIMI_MODEL_NAME", "KIMI_MODEL_API_KEY", "KIMI_MODEL_BASE_URL")):
        raise RuntimeError("KIMI_MODEL_NAME, KIMI_MODEL_API_KEY and KIMI_MODEL_BASE_URL are required")
    provider = os.environ.get("KIMI_MODEL_PROVIDER_TYPE", "openai")
    if provider not in {"kimi", "openai", "anthropic"}:
        raise ValueError("KIMI_MODEL_PROVIDER_TYPE must be kimi, openai or anthropic")
    argv = [_executable(), "--prompt", prompt, "--output-format", "stream-json"]
    if not allow_tools:
        raise RuntimeError("Kimi prompt mode enables tools automatically; explicit allow_tools=True is required")
    with tempfile.TemporaryDirectory(prefix="abx-kimi-turn-") as state:
        env = os.environ.copy()
        # The process receives only its documented model credentials, never cloud/registry tokens.
        for name in list(env):
            if any(word in name.upper() for word in ("SECRET", "TOKEN", "API_KEY", "ACCESS_KEY", "PASSWORD")) and not name.startswith("KIMI_MODEL_"):
                env.pop(name, None)
        env.update(KIMI_CODE_HOME=state, KIMI_MODEL_PROVIDER_TYPE=provider, CI="1")
        return _run(argv, timeout=command_timeout, cwd=cwd, env=env)


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
