"""Pinned upstream NousResearch Hermes CLI with bounded headless execution."""
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

PINNED_VERSION = "0.22.1"
PINNED_COMMIT = "297552a9d646119871391d202509822cd86330df"


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
    path = shutil.which("hermes")
    if not path:
        raise RuntimeError("Hermes CLI is missing; build the pinned hermes-agent template")
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


@command("hermes_version", description="Read the upstream Hermes CLI version without authentication.")
def hermes_version() -> str:
    return _run([_executable(), "--version"], timeout=30).strip()


@command("hermes_setup_check", description="Inspect CLI and provider key availability without writing configuration.")
def hermes_setup_check() -> dict:
    installed = shutil.which("hermes") is not None
    return {"installed": installed, "version": hermes_version() if installed else "",
            "pinned_version": PINNED_VERSION, "pinned_commit": PINNED_COMMIT,
            "api_key_set": bool(os.environ.get("OPENROUTER_API_KEY" if os.environ.get("HERMES_PROVIDER", "openrouter") == "openrouter" else "OPENAI_API_KEY", "").strip()),
            "workspace": _workdir()}


@command("hermes", description="Run the real Hermes agent with file and terminal tools; tool approvals are bypassed inside the sandbox.")
def hermes(prompt: str, model: str = "", provider: str = "", cwd: str = "",
           max_turns: int = 20, command_timeout: int = 600) -> str:
    if not prompt.strip():
        raise ValueError("prompt must not be empty")
    provider = provider or os.environ.get("HERMES_PROVIDER") or "openrouter"
    if provider not in {"openrouter", "openai-api", "custom"}:
        raise ValueError("provider must be openrouter, openai-api or custom")
    if not 1 <= command_timeout <= 1800 or not 1 <= max_turns <= 100:
        raise ValueError("command_timeout must be 1..1800 seconds and max_turns must be 1..100")
    selected_model = model or os.environ.get("HERMES_MODEL", "")
    if not selected_model.strip():
        raise ValueError("model or HERMES_MODEL is required")
    key_name = "OPENROUTER_API_KEY" if provider == "openrouter" else "OPENAI_API_KEY"
    if not os.environ.get(key_name, "").strip():
        raise RuntimeError(key_name + " is required; interactive login is disabled")
    env = os.environ.copy()
    env["TERMINAL_ENV"] = "local"
    env["TERMINAL_CWD"] = _workdir(cwd)
    env["CI"] = "1"
    argv = [_executable(), "chat", "-Q", "--yolo", "-q", prompt,
            "--provider", provider, "--model", selected_model,
            "--toolsets", "terminal,file", "--max-turns", str(max_turns),
            "--ignore-user-config", "--ignore-rules"]
    if provider == "custom":
        base_url = os.environ.get("OPENAI_BASE_URL", "").strip()
        if not base_url:
            raise RuntimeError("OPENAI_BASE_URL is required for provider custom")
        argv.extend(["--base-url", base_url])
    return _run(argv, timeout=command_timeout, cwd=cwd, env=env)


@command("run", description="Run a local Python script (compatibility command).")
def run(script: str = "main.py") -> str:
    return _run([sys.executable, script], timeout=120)


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
