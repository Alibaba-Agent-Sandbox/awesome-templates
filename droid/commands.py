"""Bounded, non-interactive Factory Droid commands. No credentials are returned."""
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

PACKAGE = "@factory/cli"
PINNED_VERSION = "0.241.1"


def _redact(text: str) -> str:
    secrets = {value for name, value in os.environ.items() if value and any(
        part in name.upper() for part in ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")
    )}
    for secret in sorted(secrets, key=len, reverse=True):
        for variant in (json.dumps(secret)[1:-1], json.dumps(secret, ensure_ascii=False)[1:-1], secret):
            text = text.replace(variant, "[REDACTED]")
    return text


def _workspace() -> Path:
    explicit = os.environ.get("WORKSPACE", "").strip()
    root = Path(explicit) if explicit else Path("/home/user/app")
    if not explicit and not root.is_dir():
        root = Path.cwd()
    if not root.is_dir():
        raise ValueError("WORKSPACE must name an existing directory")
    return root.resolve()


def _workdir(cwd: str = "") -> Path:
    root = _workspace()
    path = (root / cwd).resolve() if cwd else root
    if not path.is_relative_to(root) or not path.is_dir():
        raise ValueError("cwd must be an existing directory inside WORKSPACE")
    return path


def _executable() -> str:
    executable = shutil.which("droid")
    if not executable:
        raise RuntimeError("droid CLI was not found on PATH; install @factory/cli@0.241.1")
    return executable


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
        raise RuntimeError(f"droid timed out after {timeout} seconds") from None
    return (process.returncode, b"".join(stdout_parts).decode("utf-8", "replace"),
            b"".join(stderr_parts).decode("utf-8", "replace"))


def _run(args: list[str], cwd: Path, timeout: int) -> str:
    env = os.environ.copy()
    env["FACTORY_DROID_AUTO_UPDATE_ENABLED"] = "false"
    try:
        code, stdout, stderr = _run_process(
            [_executable(), *args], cwd=str(cwd), timeout=timeout, env=env,
        )
    except OSError:
        raise RuntimeError("droid could not start; check executable and workspace permissions") from None
    if code != 0:
        detail = _redact((stderr or stdout).strip())
        raise RuntimeError(detail or f"droid exited {code}")
    return _redact(stdout)


@command("droid_version", description="Read the installed Droid CLI version without a model call.")
def droid_version() -> str:
    return _run(["--version"], _workspace(), 30).strip()


@command("droid_setup_check", description="Inspect CLI installation and key presence without a model call.")
def droid_setup_check() -> dict:
    installed = shutil.which("droid") is not None
    return {
        "installed": installed,
        "package": PACKAGE,
        "version": droid_version() if installed else "",
        "expected_version": PINNED_VERSION,
        "api_key_set": bool(os.environ.get("FACTORY_API_KEY", "").strip()),
        "workspace_exists": _workspace().is_dir(),
        "auto_update_enabled": False,
    }


@command("droid", description="Run Factory Droid headless inside WORKSPACE with an execution deadline.")
def droid(prompt: str, auto: str = "low", cwd: str = "", command_timeout: int = 300) -> str:
    """Run argv directly; low autonomy permits project edits without unsafe bypass."""
    if not prompt.strip():
        raise ValueError("prompt must not be empty")
    if auto not in {"", "low", "medium", "high"}:
        raise ValueError("auto must be empty, low, medium, or high")
    if isinstance(command_timeout, bool) or not isinstance(command_timeout, int) or not 1 <= command_timeout <= 600:
        raise ValueError("command_timeout must be an integer from 1 to 600 seconds")
    workdir = _workdir(cwd)
    if not os.environ.get("FACTORY_API_KEY", "").strip():
        raise RuntimeError("FACTORY_API_KEY is required; interactive login is disabled for named commands")
    args = ["exec"]
    if auto:
        args.extend(["--auto", auto])
    # The option terminator keeps prompts beginning with '-' as literal text.
    args.extend(["--", prompt])
    return _run(args, workdir, command_timeout)


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
