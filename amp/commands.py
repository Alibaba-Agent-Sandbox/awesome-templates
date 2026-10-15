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
import shutil
import subprocess
from pathlib import Path

from agent_sandbox.server import command, start

PACKAGE = "@ampcode/cli"
SETTINGS_KEYS = {
    "amp.dangerouslyAllowAll": True,
    "amp.updates.mode": "disabled",
    "amp.notifications.enabled": False,
}
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


def _ensure_settings() -> dict:
    path = _settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict = {}
    if path.is_file():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Amp settings file is not JSON: {path}") from exc
        if not isinstance(loaded, dict):
            raise RuntimeError(f"Amp settings file must be a JSON object: {path}")
        data = loaded
    data.update(SETTINGS_KEYS)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return data


def _redact(text: str) -> str:
    key = os.environ.get("AMP_API_KEY", "")
    if key:
        text = text.replace(key, "***")
    return text.strip()


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


def _run_amp(args: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    _ensure_settings()
    env = os.environ.copy()
    env["AMP_SETTINGS_FILE"] = str(_settings_path())
    try:
        return subprocess.run(
            [_amp_executable(), *args],
            cwd=_workdir(),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"amp timed out after {timeout} seconds") from exc


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
    return _version_token(result.stdout)


@command("amp_version", description="Print the installed Amp CLI version (amp version).")
def amp_version() -> str:
    """Return the version token from ``amp version``. Does not need ``AMP_API_KEY``."""
    return _read_version()


@command(
    "amp_setup_check",
    description="Report whether amp is installed, write settings, and whether AMP_API_KEY is set.",
)
def amp_setup_check() -> dict:
    """Write Amp settings and report install state. Does not call ``amp -x``."""
    settings = _ensure_settings()
    installed = shutil.which("amp") is not None
    version = _read_version() if installed else ""
    return {
        "installed": installed,
        "package": PACKAGE,
        "version": version,
        "api_key_set": bool(os.environ.get("AMP_API_KEY", "").strip()),
        "settings_path": str(_settings_path()),
        "dangerously_allow_all": bool(settings.get("amp.dangerouslyAllowAll")),
        "updates_mode": str(settings.get("amp.updates.mode")),
    }


def _execute(prompt: str, stream_json: bool = False) -> str:
    text = prompt.strip()
    if not text:
        raise ValueError("prompt is required")
    _require_key()
    argv = [
        "--dangerously-allow-all",
        "--no-color",
        "--no-notifications",
        "--no-ide",
    ]
    if stream_json:
        argv.append("--stream-json")
    argv.extend(["-x", text])
    result = _run_amp(argv, timeout=600)
    if result.returncode != 0:
        detail = _redact(result.stderr or result.stdout or "")
        raise RuntimeError(detail or f"amp exited {result.returncode}")
    return result.stdout


@command(
    "amp_execute",
    description="Run amp -x. Requires AMP_API_KEY. Optional stream_json adds --stream-json.",
)
def amp_execute(prompt: str, stream_json: bool = False) -> str:
    """Run execute mode. ``stream_json`` returns the full JSONL stdout after exit."""
    return _execute(prompt, stream_json=stream_json)


@command("amp", description="Previous name for amp_execute. Same arguments.")
def amp(prompt: str, stream_json: bool = False) -> str:
    """Backward-compatible name. The directory used to register only this command."""
    return _execute(prompt, stream_json=stream_json)


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
