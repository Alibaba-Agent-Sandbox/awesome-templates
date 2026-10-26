"""Official Goose CLI, isolated configuration and explicit tool execution."""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from urllib.parse import urlsplit
from agent_sandbox.server import command, start
import signal
import subprocess
import threading
import time

VERSION = "1.54.0"


# Generated from scripts/process_runners/file.py; update with scripts/sync_process_runners.py.
def _run_process(argv: list[str], *, cwd: str, timeout: int | float,
                 env: dict | None = None, input_file=None) -> tuple[int, str, str]:
    """Keep the Linux session leader unreaped until its owned group is stopped."""
    process = subprocess.Popen(argv, cwd=cwd, env=env,
        stdin=input_file if input_file is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    stdout_parts: list[bytes] = []
    stderr_parts: list[bytes] = []
    overflow = threading.Event()
    def drain(stream, parts):
        size = 0
        try:
            while chunk := stream.read(65536):
                size += len(chunk)
                if size > 256 * 1024:
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
        raise RuntimeError("command output exceeded the 256 KiB per-stream limit") from None
    if timed_out:
        raise RuntimeError(f"command timed out after {timeout} seconds") from None
    return (process.returncode, b"".join(stdout_parts).decode("utf-8", "replace"),
            b"".join(stderr_parts).decode("utf-8", "replace"))


def _binary() -> str:
    candidate = os.environ.get("GOOSE_BINARY") or shutil.which("goose")
    if not candidate:
        raise RuntimeError("pinned Goose executable is unavailable")
    path = Path(candidate).resolve(strict=True)
    if not path.is_file() or not os.access(path, os.X_OK):
        raise RuntimeError("pinned Goose executable is unavailable")
    return str(path)


def _workspace(cwd: str = "") -> Path:
    root = Path(os.environ.get("WORKSPACE", "/home/user/app")).resolve(strict=True)
    if not isinstance(cwd, str) or "\x00" in cwd or len(cwd.encode()) > 4096:
        raise ValueError("cwd must be a bounded workspace directory")
    target = Path(cwd) if cwd else root
    if not target.is_absolute():
        target = root / target
    target = target.resolve(strict=True)
    if not target.is_dir() or not target.is_relative_to(root):
        raise ValueError("cwd must stay inside WORKSPACE")
    return target


def _environment(private: str) -> dict[str, str]:
    env = {name: os.environ[name] for name in ("PATH", "SSL_CERT_FILE", "SSL_CERT_DIR") if name in os.environ}
    env.update(HOME=private, XDG_CONFIG_HOME=private + "/config", XDG_DATA_HOME=private + "/data",
        XDG_STATE_HOME=private + "/state", GOOSE_PATH_ROOT=private, LANG="C.UTF-8", LC_ALL="C.UTF-8",
        GOOSE_DISABLE_KEYRING="1", GOOSE_TELEMETRY_ENABLED="false", GOOSE_DISABLE_SESSION_NAMING="true",
        CONTEXT_FILE_NAMES="[]", GOOSE_TOOLSHIM="false", NO_COLOR="1")
    return env


@command("goose_version", description="Inspect the actual official pinned Goose binary without model calls or caller configuration changes.")
def goose_version() -> str:
    with tempfile.TemporaryDirectory(prefix="abx-goose-version-") as private:
        code, output, _ = _run_process([_binary(), "--version"], cwd=private, timeout=20, env=_environment(private))
    if code or output.strip() != VERSION:
        raise RuntimeError("actual Goose executable does not match1.54.0")
    return VERSION


@command("goose_setup_check", description="Read-only binary/configuration diagnostic; returns booleans without credentials or login.")
def goose_setup_check() -> dict:
    installed = bool(os.environ.get("GOOSE_BINARY") or shutil.which("goose"))
    return {"installed": installed, "version": goose_version() if installed else "",
        "api_key_set": bool(os.environ.get("GOOSE_API_KEY", "").strip()),
        "base_url_set": bool(os.environ.get("GOOSE_BASE_URL", "").strip()),
        "model_set": bool(os.environ.get("GOOSE_MODEL", "").strip())}


@command("goose", description="Run the actual Goose CLI with file stdin and private config. Tools require explicit allow_tools=true.")
def goose(prompt: str, cwd: str = "", allow_tools: bool = False, command_timeout: int = 600) -> dict:
    if not isinstance(prompt, str) or not prompt.strip() or "\x00" in prompt or len(prompt.encode()) > 256 * 1024:
        raise ValueError("prompt must be nonempty UTF-8 without NUL, at most256KiB")
    if not isinstance(allow_tools, bool):
        raise ValueError("allow_tools must be a boolean")
    if isinstance(command_timeout, bool) or not isinstance(command_timeout, int) or not 1 <= command_timeout <= 1800:
        raise ValueError("command_timeout must be1..1800 seconds")
    settings = {name: os.environ.get(name, "").strip() for name in ("GOOSE_API_KEY", "GOOSE_BASE_URL", "GOOSE_MODEL")}
    if not all(settings.values()):
        raise RuntimeError("GOOSE_API_KEY, GOOSE_BASE_URL and GOOSE_MODEL are required; interactive configuration is disabled")
    endpoint = urlsplit(settings["GOOSE_BASE_URL"])
    if endpoint.scheme not in {"http", "https"} or not endpoint.hostname or endpoint.username or endpoint.password or endpoint.query or endpoint.fragment:
        raise ValueError("GOOSE_BASE_URL must be an HTTP(S) endpoint without credentials, query or fragment")
    target = _workspace(cwd)
    goose_version()
    with tempfile.TemporaryDirectory(prefix="abx-goose-config-") as private:
        env = _environment(private)
        env.update(GOOSE_PROVIDER="openai", GOOSE_MODEL=settings["GOOSE_MODEL"],
            OPENAI_API_KEY=settings["GOOSE_API_KEY"], OPENAI_BASE_URL=settings["GOOSE_BASE_URL"],
            GOOSE_MODE="auto" if allow_tools else "chat")
        argv = [_binary(), "run", "--instructions", "-", "--no-session", "--no-profile", "--max-turns", "20",
            "--quiet", "--output-format", "text", "--provider", "openai", "--model", settings["GOOSE_MODEL"]]
        if allow_tools:
            argv += ["--with-builtin", "developer"]
        with tempfile.TemporaryFile(dir=private) as source:
            source.write(prompt.encode()); source.seek(0)
            code, output, error = _run_process(argv, cwd=str(target), timeout=command_timeout, env=env, input_file=source)
    for value in (settings["GOOSE_API_KEY"], settings["GOOSE_BASE_URL"]):
        output = output.replace(value, "[REDACTED]"); error = error.replace(value, "[REDACTED]")
    return {"stdout": output, "stderr": error, "exit_code": code}


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
