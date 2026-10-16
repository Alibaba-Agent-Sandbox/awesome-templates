"""Pinned official Pi CLI with isolated ephemeral OpenAI-compatible configuration."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

from agent_sandbox.server import command, start

PINNED_VERSION = "1.3.0"


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
    path = shutil.which("pi")
    if not path:
        raise RuntimeError("Pi CLI is missing; install @earendil-works/pi-coding-agent@1.3.0")
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
        raise RuntimeError(f"command timed out after {timeout} seconds") from None
    return (process.returncode, b"".join(stdout_parts).decode("utf-8", "replace"),
            b"".join(stderr_parts).decode("utf-8", "replace"))


def _run(argv: list[str], *, timeout: int, cwd: str = "", env: dict | None = None, input_text: str | None = None) -> str:
    code, stdout, stderr = _run_process(argv, cwd=_workdir(cwd), timeout=timeout, env=env, input_text=input_text)
    if code:
        raise RuntimeError(_redact(stderr or stdout) or f"command exited {code}")
    return _redact(stdout)


@command("pi_version", description="Read the installed official Pi CLI version without credentials.")
def pi_version() -> str:
    return _run([_executable(), "--version"], timeout=30).strip()


@command("pi_setup_check", description="Inspect Pi and compatible-model settings without exposing credentials.")
def pi_setup_check() -> dict:
    installed = shutil.which("pi") is not None
    return {
        "installed": installed,
        "version": pi_version() if installed else "",
        "pinned_version": PINNED_VERSION,
        "api_key_set": bool(os.environ.get("PI_API_KEY", "").strip()),
        "base_url_set": bool(os.environ.get("PI_BASE_URL", "").strip()),
        "model_set": bool(os.environ.get("PI_MODEL", "").strip()),
        "workspace": _workdir(),
    }


@command("pi", description="Run official Pi print mode; allow_tools explicitly permits sandbox file edits and bash.")
def pi(prompt: str, cwd: str = "", allow_tools: bool = False, command_timeout: int = 600) -> str:
    """One ephemeral turn. Tool selection is the permission boundary, not --no-approve."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt must not be empty")
    if not isinstance(allow_tools, bool):
        raise ValueError("allow_tools must be a boolean")
    if isinstance(command_timeout, bool) or not isinstance(command_timeout, int) or not 1 <= command_timeout <= 1800:
        raise ValueError("command_timeout must be between 1 and 1800 seconds")
    settings = {name: os.environ.get(name, "").strip() for name in ("PI_BASE_URL", "PI_MODEL", "PI_API_KEY")}
    if not all(settings.values()):
        raise RuntimeError("PI_BASE_URL, PI_MODEL and PI_API_KEY are required; interactive login is disabled")
    from urllib.parse import urlsplit
    endpoint = urlsplit(settings["PI_BASE_URL"])
    if endpoint.scheme not in {"http", "https"} or not endpoint.hostname or endpoint.username or endpoint.password or endpoint.query or endpoint.fragment:
        raise ValueError("PI_BASE_URL must be an HTTP(S) endpoint without embedded credentials, query or fragment")
    executable = _executable()
    directory = _workdir(cwd)
    with tempfile.TemporaryDirectory(prefix="abx-pi-config-") as config:
        # No auth.json, user/project settings, command-valued API keys or extensions.
        models = {"providers": {"abx": {"baseUrl": settings["PI_BASE_URL"],
            "api": "openai-completions", "apiKey": "$PI_API_KEY",
            "models": [{"id": settings["PI_MODEL"]}]}}}
        Path(config, "models.json").write_text(json.dumps(models))
        env = os.environ.copy()
        env.update({"PI_CODING_AGENT_DIR": config, "PI_OFFLINE": "1", "PI_TELEMETRY": "0", "CI": "1"})
        tools = "read,grep,find,ls,edit,write,bash" if allow_tools else "read,grep,find,ls"
        return _run([executable, "--print", "--mode", "text", "--no-session", "--offline",
            "--no-approve", "--no-extensions", "--no-mcp", "--no-skills", "--no-prompt-templates",
            "--no-themes", "--no-context-files", "--provider", "abx", "--model", settings["PI_MODEL"],
            "--tools", tools], timeout=command_timeout, cwd=directory, env=env, input_text=prompt)


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
