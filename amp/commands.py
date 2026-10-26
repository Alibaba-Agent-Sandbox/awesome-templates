"""Sourcegraph Amp CLI commands.

Package ``@ampcode/cli`` provides the ``amp`` binary. Probed 2026-10-15 at
``0.0.1792022479-ge66e24``:

- ``amp version`` prints the version and does not need a key.
- ``amp -x <prompt>`` is execute mode. ``--stream-json`` adds JSONL on stdout.
- ``--dangerously-allow-all`` is accepted by that binary. ``amp --help`` does
  not list it; the documented switch is the settings key
  ``amp.dangerouslyAllowAll``.
- With no ``AMP_API_KEY``, ``amp -x`` starts a device login and waits. These
  commands do not start that flow.

``AMP_API_KEY`` is an Amp access token. DashScope and other OpenAI-compatible
keys are not read and are not accepted by the CLI.
"""
from __future__ import annotations

import json
import os
import signal
import shutil
import subprocess
import threading
import time
from pathlib import Path

from agent_sandbox.server import command, start

PACKAGE = "@ampcode/cli"
_MISSING_KEY = (
    "AMP_API_KEY is required to run amp -x. Create an access token at "
    "https://ampcode.com/settings/security#access-token and pass it as AMP_API_KEY. "
    "Amp does not accept a DashScope, OpenAI, or Anthropic key. "
    "When AMP_API_KEY is unset, the amp CLI starts a device-login flow and waits; "
    "this command does not start that flow."
)


def _settings_path() -> Path:
    explicit = os.environ.get("AMP_SETTINGS_FILE", "").strip()
    if explicit:
        return Path(explicit)
    workspace = os.environ.get("WORKSPACE", "").strip()
    if workspace and os.path.isdir(workspace):
        return Path(workspace) / ".e2e_amp" / "settings.json"
    home = Path(os.environ.get("HOME") or "/home/user")
    # The image sets HOME=/home/user. Anywhere else, keep the file next to the
    # process so a laptop run does not rewrite ~/.config/amp/settings.json.
    if home == Path("/home/user"):
        return home / ".config" / "amp" / "settings.json"
    return Path.cwd() / ".e2e_amp" / "settings.json"


def _read_settings() -> dict:
    """Inspect configuration without creating or changing it."""
    path = _settings_path()
    if path.is_file():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Amp settings file is not JSON: {path}") from exc
        if not isinstance(loaded, dict):
            raise RuntimeError(f"Amp settings file must be a JSON object: {path}")
        return loaded
    return {}


def _redact(text: str) -> str:
    secrets = {
        value for name, value in os.environ.items()
        if value and any(part in name.upper() for part in
                         ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL"))
    }
    for secret in sorted(secrets, key=len, reverse=True):
        text = text.replace(json.dumps(secret)[1:-1], "[REDACTED]")
        text = text.replace(secret, "[REDACTED]")
    return text


def _require_key() -> None:
    if not os.environ.get("AMP_API_KEY", "").strip():
        raise RuntimeError(_MISSING_KEY)


def _amp_executable() -> str:
    found = shutil.which("amp")
    if not found:
        raise RuntimeError(
            "amp CLI was not found on PATH. The image installs "
            f"{PACKAGE} (npm bin name amp)."
        )
    return found


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
        raise RuntimeError(f"amp timed out after {timeout} seconds") from None
    return (process.returncode, b"".join(stdout_parts).decode("utf-8", "replace"),
            b"".join(stderr_parts).decode("utf-8", "replace"))


def _run_amp(args: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["AMP_SETTINGS_FILE"] = str(_settings_path())
    argv = [_amp_executable(), *args]
    code, stdout, stderr = _run_process(argv, cwd=_workdir(), timeout=timeout, env=env)
    return subprocess.CompletedProcess(argv, code, stdout, stderr)


def _workdir() -> str:
    for candidate in (os.environ.get("WORKSPACE"), "/home/user/app", os.getcwd()):
        if candidate and os.path.isdir(candidate):
            return candidate
    return os.getcwd()


def _version_token(stdout: str) -> str:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("amp version printed no output")
    token = lines[0].split()[0]
    if not token:
        raise RuntimeError("amp version did not print a version token")
    return token


def _read_version() -> str:
    result = _run_amp(["version"], timeout=60)
    if result.returncode != 0:
        detail = _redact(result.stderr or result.stdout or "")
        raise RuntimeError(detail or f"amp version exited {result.returncode}")
    return _redact(_version_token(result.stdout))


@command("amp_version", description="Print the installed Amp CLI version (amp version).")
def amp_version() -> str:
    """Return the version token from ``amp version``. Does not need ``AMP_API_KEY``."""
    return _read_version()


@command(
    "amp_setup_check",
    description="Inspect the Amp installation, settings, and key presence without changing settings.",
)
def amp_setup_check() -> dict:
    """Read Amp settings and report install state. Does not call ``amp -x``."""
    settings = _read_settings()
    installed = shutil.which("amp") is not None
    version = _read_version() if installed else ""
    return {
        "installed": installed,
        "package": PACKAGE,
        "version": version,
        "api_key_set": bool(os.environ.get("AMP_API_KEY", "").strip()),
        "settings_path": str(_settings_path()),
        "settings_exists": _settings_path().is_file(),
        "dangerously_allow_all": settings.get("amp.dangerouslyAllowAll") is True,
        "updates_mode": str(settings.get("amp.updates.mode", "default")),
    }


def _execute(prompt: str, stream_json: bool = False, dangerously_allow_all: bool = False) -> str:
    text = prompt.strip()
    if not text:
        raise ValueError("prompt is required")
    _require_key()
    argv = [
        "--no-color",
        "--no-notifications",
        "--no-ide",
    ]
    if dangerously_allow_all:
        argv.append("--dangerously-allow-all")
    if stream_json:
        argv.append("--stream-json")
    argv.extend(["-x", text])
    result = _run_amp(argv, timeout=600)
    if result.returncode != 0:
        detail = _redact(result.stderr or result.stdout or "")
        raise RuntimeError(detail or f"amp exited {result.returncode}")
    return _redact(result.stdout)


@command(
    "amp_execute",
    description="Run amp -x. Requires AMP_API_KEY. Optional stream_json adds --stream-json.",
)
def amp_execute(prompt: str, stream_json: bool = False, dangerously_allow_all: bool = False) -> str:
    """Run execute mode. ``stream_json`` returns the full JSONL stdout after exit."""
    return _execute(prompt, stream_json=stream_json, dangerously_allow_all=dangerously_allow_all)


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
