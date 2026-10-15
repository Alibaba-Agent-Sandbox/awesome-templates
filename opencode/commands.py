"""Named commands for the OpenCode coding agent.

The primary command is ``opencode_run``. It executes ``opencode run`` as an
argv list and returns one JSON object. ``opencode serve`` is a second HTTP
server on port 4096, started only by ``opencode_serve_start``.

``start()`` runs only under ``python3 commands.py``. ``agent-sandbox-server
serve --commands`` imports this module.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from agent_sandbox.server import command, start

PINNED_VERSION = "1.19.0"
DEFAULT_MODEL = "dashscope/qwen3.8-flash"
RUN_TIMEOUT_S = 600
SERVE_READY_S = 20
STATE_PATH = Path("/tmp/opencode-serve.json")
LOG_PATH = Path("/tmp/opencode-serve.log")
IMAGE_CONFIG = Path("/home/user/app/opencode.json")


def _redact(text: str) -> str:
    redacted = text
    for key, value in os.environ.items():
        if not value or len(value) < 8:
            continue
        upper = key.upper()
        if any(part in upper for part in ("KEY", "SECRET", "TOKEN", "PASSWORD")):
            redacted = redacted.replace(value, "***")
    return redacted


def _resolved_model(model: str) -> str:
    chosen = (model or os.environ.get("OPENCODE_MODEL") or DEFAULT_MODEL).strip()
    return chosen or DEFAULT_MODEL


def _config_file() -> Path:
    candidates: list[Path] = []
    override = os.environ.get("OPENCODE_CONFIG", "").strip()
    if override:
        candidates.append(Path(override))
    candidates.append(IMAGE_CONFIG)
    candidates.append(Path.cwd() / "opencode.json")
    for path in candidates:
        if path.is_file():
            return path
    raise RuntimeError("opencode.json was not found")


def _load_config(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"opencode.json is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("opencode.json must be a JSON object")
    return data


def _assert_dashscope(data: dict) -> None:
    provider = data.get("provider")
    if not isinstance(provider, dict):
        raise RuntimeError("opencode.json has no provider object")
    dashscope = provider.get("dashscope")
    if not isinstance(dashscope, dict):
        raise RuntimeError("opencode.json has no dashscope provider")
    if dashscope.get("npm") != "@ai-sdk/openai-compatible":
        raise RuntimeError("dashscope provider must use @ai-sdk/openai-compatible")
    options = dashscope.get("options")
    if not isinstance(options, dict):
        raise RuntimeError("dashscope provider has no options")
    if options.get("baseURL") != "{env:ABX_LLM_BASE_URL}":
        raise RuntimeError("dashscope baseURL must be {env:ABX_LLM_BASE_URL}")
    if options.get("apiKey") != "{env:ABX_LLM_API_KEY}":
        raise RuntimeError("dashscope apiKey must be {env:ABX_LLM_API_KEY}")
    models = dashscope.get("models")
    if not isinstance(models, dict) or "qwen3.8-flash" not in models:
        raise RuntimeError("dashscope models must include qwen3.8-flash")


def _child_config(model: str) -> tuple[str, Path | None]:
    """Return ``(config path, temp dir to delete)`` for one CLI child."""
    base = _config_file()
    provider, _, model_id = model.partition("/")
    if provider != "dashscope" or not model_id:
        return str(base), None
    data = _load_config(base)
    models = (
        data.setdefault("provider", {})
        .setdefault("dashscope", {})
        .setdefault("models", {})
    )
    if not isinstance(models, dict) or model_id in models:
        return str(base), None
    models[model_id] = {"name": model_id}
    directory = Path(tempfile.mkdtemp(prefix="opencode-config-"))
    path = directory / "opencode.json"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return str(path), directory


def _workdir(cwd: str) -> str:
    raw = (cwd or "").strip()
    if not raw:
        default = "/home/user/app"
        return default if os.path.isdir(default) else os.getcwd()
    path = Path(raw)
    if not path.is_dir():
        raise ValueError(f"cwd is not a directory: {raw}")
    return str(path.resolve())


def _run(argv: list[str], *, cwd: str, timeout: int, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            argv,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("opencode CLI was not found on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"opencode timed out after {timeout} seconds") from exc


def _require_ok(result: subprocess.CompletedProcess[str], what: str) -> str:
    if result.returncode != 0:
        detail = _redact((result.stderr or result.stdout or "").strip())
        raise RuntimeError(detail or f"{what} exited {result.returncode}")
    return result.stdout


def _parse_events(stdout: str) -> tuple[str, str]:
    texts: list[str] = []
    session_id = ""
    for line in stdout.splitlines():
        stripped = line.strip()
        if not stripped.startswith("{"):
            continue
        try:
            event = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        if not session_id and isinstance(event.get("sessionID"), str):
            session_id = event["sessionID"]
        if event.get("type") != "text":
            continue
        part = event.get("part")
        if isinstance(part, dict) and isinstance(part.get("text"), str):
            texts.append(part["text"])
    return "".join(texts), session_id


def _execute_run(
    prompt: str,
    model: str,
    agent: str,
    session: str,
    continue_session: bool,
    cwd: str,
) -> dict[str, str]:
    text = prompt.strip()
    if not text:
        raise ValueError("prompt is required")
    chosen = _resolved_model(model)
    workdir = _workdir(cwd)
    config_path, temp_dir = _child_config(chosen)
    env = os.environ.copy()
    env["OPENCODE_CONFIG"] = config_path
    env["OPENCODE_DISABLE_AUTOUPDATE"] = "true"
    env["OPENCODE_MODEL"] = chosen
    argv = [
        "opencode",
        "run",
        "--pure",
        "--format",
        "json",
        "--auto",
        "--model",
        chosen,
        "--dir",
        workdir,
    ]
    agent_name = agent.strip()
    if agent_name:
        argv.extend(["--agent", agent_name])
    session_arg = session.strip()
    if session_arg:
        argv.extend(["--session", session_arg])
    if continue_session:
        argv.append("--continue")
    argv.append(text)
    try:
        result = _run(argv, cwd=workdir, timeout=RUN_TIMEOUT_S, env=env)
    finally:
        if temp_dir is not None:
            for child in temp_dir.iterdir():
                child.unlink(missing_ok=True)
            temp_dir.rmdir()
    stdout = _require_ok(result, "opencode run")
    visible, session_id = _parse_events(stdout)
    return {
        "text": visible,
        "stdout": stdout,
        "session_id": session_id,
        "model": chosen,
        "agent": agent_name,
        "cwd": workdir,
    }


def _version_text() -> str:
    result = _run(["opencode", "--version"], cwd=os.getcwd(), timeout=30)
    return _require_ok(result, "opencode --version").strip()


def _read_state() -> dict | None:
    if not STATE_PATH.is_file():
        return None
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _healthy(port: int) -> bool:
    url = f"http://127.0.0.1:{port}/global/health"
    try:
        with urllib.request.urlopen(url, timeout=1) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return False
    return isinstance(body, dict) and body.get("healthy") is True


def _serve_status() -> dict[str, object]:
    state = _read_state() or {}
    pid = int(state.get("pid") or 0)
    port = int(state.get("port") or 0)
    hostname = str(state.get("hostname") or "")
    alive = _pid_alive(pid)
    healthy = _healthy(port) if alive and port else False
    if not alive and STATE_PATH.is_file():
        STATE_PATH.unlink(missing_ok=True)
    return {
        "running": alive and healthy,
        "port": port if alive else 0,
        "hostname": hostname if alive else "",
        "pid": pid if alive else 0,
        "healthy": healthy,
    }


def _stop_serve() -> None:
    state = _read_state()
    if not state:
        return
    pid = int(state.get("pid") or 0)
    if _pid_alive(pid):
        try:
            os.killpg(pid, signal.SIGTERM)
        except OSError:
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and _pid_alive(pid):
            time.sleep(0.1)
        if _pid_alive(pid):
            try:
                os.killpg(pid, signal.SIGKILL)
            except OSError:
                pass
    STATE_PATH.unlink(missing_ok=True)


@command("opencode_run", description="Run OpenCode headless (opencode run --format json).")
def opencode_run(
    prompt: str,
    model: str = "",
    agent: str = "",
    session: str = "",
    continue_session: bool = False,
    cwd: str = "",
) -> dict[str, str]:
    """One ``opencode run``. ``continue_session`` maps to ``--continue``."""
    return _execute_run(prompt, model, agent, session, continue_session, cwd)


@command(
    "opencode",
    description="Compatibility alias of opencode_run. Returns the raw JSON-event stdout.",
)
def opencode(
    prompt: str,
    model: str = "",
    agent: str = "",
    session: str = "",
    continue_session: bool = False,
    cwd: str = "",
) -> str:
    """Same argv as ``opencode_run``. Prefer ``opencode_run`` for the parsed text."""
    return _execute_run(prompt, model, agent, session, continue_session, cwd)["stdout"]


@command("opencode_version", description="Print the pinned opencode version.")
def opencode_version() -> str:
    """Return ``opencode --version`` with surrounding whitespace removed."""
    found = _version_text()
    if found != PINNED_VERSION:
        raise RuntimeError(f"opencode version {found} does not match pin {PINNED_VERSION}")
    return found


@command("opencode_setup_check", description="Check the opencode binary and DashScope config.")
def opencode_setup_check() -> str:
    """Return ``ok`` when the pin and ``opencode.json`` match this template."""
    found = _version_text()
    if found != PINNED_VERSION:
        raise RuntimeError(f"opencode version {found} does not match pin {PINNED_VERSION}")
    _assert_dashscope(_load_config(_config_file()))
    return "ok"


@command("opencode_serve_start", description="Start opencode serve and wait until it is healthy.")
def opencode_serve_start(port: int = 4096, hostname: str = "0.0.0.0") -> dict[str, object]:
    """Bind ``opencode serve`` and return when ``/global/health`` is healthy."""
    if port < 1 or port > 65535:
        raise ValueError("port must be between 1 and 65535")
    host = hostname.strip()
    if not host:
        raise ValueError("hostname is required")
    current = _serve_status()
    if current["running"]:
        if int(current["port"]) != port:
            raise RuntimeError(f"opencode serve is already running on port {current['port']}")
        return current
    _stop_serve()
    config_path, _temp = _child_config(DEFAULT_MODEL)
    env = os.environ.copy()
    env["OPENCODE_CONFIG"] = config_path
    env["OPENCODE_DISABLE_AUTOUPDATE"] = "true"
    argv = [
        "opencode",
        "serve",
        "--pure",
        "--hostname",
        host,
        "--port",
        str(port),
    ]
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log = open(LOG_PATH, "ab")
    try:
        proc = subprocess.Popen(
            argv,
            cwd=_workdir(""),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
    except FileNotFoundError as exc:
        log.close()
        raise RuntimeError("opencode CLI was not found on PATH") from exc
    log.close()
    STATE_PATH.write_text(
        json.dumps({"pid": proc.pid, "port": port, "hostname": host}) + "\n",
        encoding="utf-8",
    )
    deadline = time.monotonic() + SERVE_READY_S
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            tail = ""
            if LOG_PATH.is_file():
                tail = _redact(LOG_PATH.read_text(encoding="utf-8", errors="replace")[-800:])
            STATE_PATH.unlink(missing_ok=True)
            raise RuntimeError(tail or f"opencode serve exited {proc.returncode}")
        if _healthy(port):
            return _serve_status()
        time.sleep(0.2)
    _stop_serve()
    raise RuntimeError(f"opencode serve did not become healthy on port {port}")


@command("opencode_serve_status", description="Report whether opencode serve is healthy.")
def opencode_serve_status() -> dict[str, object]:
    """Return the pid file plus a localhost ``/global/health`` probe."""
    return _serve_status()


@command("opencode_serve_stop", description="Stop opencode serve if this template started it.")
def opencode_serve_stop() -> str:
    """Terminate the serve process group. Does nothing when it is already stopped."""
    _stop_serve()
    return "stopped"


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
