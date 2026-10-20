"""Named commands for the OpenCode coding agent.

The primary command is ``opencode_run``. It executes ``opencode run`` as an
argv list and returns one JSON object. ``opencode serve`` is a second HTTP
server on port 4096, started only by ``opencode_serve_start``.

``start()`` runs only under ``python3 commands.py``. ``agent-sandbox-server
serve --commands`` imports this module.
"""
from __future__ import annotations

import base64
import json
import os
import signal
import subprocess
import tempfile
import time
import threading
import urllib.error
import urllib.request
from pathlib import Path

from agent_sandbox.server import command, start

PINNED_VERSION = "1.19.0"
DEFAULT_MODEL = "dashscope/qwen3.8-flash"
RUN_TIMEOUT_S = 600
SERVE_READY_S = 20
IMAGE_CONFIG = Path("/home/user/app/opencode.json")
MODULE_CONFIG = Path(__file__).resolve().with_name("opencode.json")
_SERVE_LOCK = threading.RLock()
_SERVE_PROCESS: subprocess.Popen | None = None
_SERVE_PORT = 0
_SERVE_HOST = ""
_SERVE_OWNER_PID = 0


def _redact(text: str) -> str:
    redacted = text
    for key, value in os.environ.items():
        if not value:
            continue
        upper = key.upper()
        if any(part in upper for part in ("KEY", "SECRET", "TOKEN", "PASSWORD", "CREDENTIAL")):
            redacted = redacted.replace(value, "***")
    return redacted


def _redact_event(value):
    if isinstance(value, str):
        return _redact(value)
    if isinstance(value, list):
        return [_redact_event(item) for item in value]
    if isinstance(value, dict):
        return {_redact(key): _redact_event(item) for key, item in value.items()}
    return value


def _safe_events(stdout: str) -> str:
    lines = []
    for line in stdout.splitlines():
        try:
            lines.append(json.dumps(_redact_event(json.loads(line)), ensure_ascii=False))
        except json.JSONDecodeError:
            lines.append(_redact(line))
    return "\n".join(lines) + ("\n" if stdout.endswith("\n") else "")


def _resolved_model(model: str) -> str:
    chosen = (model or os.environ.get("OPENCODE_MODEL") or DEFAULT_MODEL).strip()
    return chosen or DEFAULT_MODEL


def _config_file() -> Path:
    candidates: list[Path] = []
    override = os.environ.get("OPENCODE_CONFIG", "").strip()
    if override:
        path = Path(override)
        if not path.is_file():
            raise RuntimeError("OPENCODE_CONFIG does not point to a readable config file")
        return path
    candidates.extend((MODULE_CONFIG, Path.cwd() / "opencode.json"))
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
        return str(MODULE_CONFIG.parent)
    path = Path(raw)
    if not path.is_dir():
        raise ValueError("cwd must be an existing directory")
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
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"opencode timed out after {timeout} seconds; CLI output omitted") from None


def _require_ok(result: subprocess.CompletedProcess[str], what: str) -> str:
    if result.returncode != 0:
        # CLI failures can include prompts, tool arguments, URLs and credentials.
        # Never return their stdout/stderr in the HTTP error envelope.
        raise RuntimeError(f"{what} exited {result.returncode}; CLI output omitted")
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
    if session.strip() and continue_session:
        raise ValueError("session and continue_session are mutually exclusive")
    chosen = _resolved_model(model)
    if chosen.startswith("-") or agent.strip().startswith("-") or session.strip().startswith("-"):
        raise ValueError("model, agent and session must not start with an option prefix")
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
    argv.extend(["--", text])
    try:
        result = _run(argv, cwd=workdir, timeout=RUN_TIMEOUT_S, env=env)
    finally:
        if temp_dir is not None:
            for child in temp_dir.iterdir():
                child.unlink(missing_ok=True)
            temp_dir.rmdir()
    stdout = _safe_events(_require_ok(result, "opencode run"))
    visible, session_id = _parse_events(stdout)
    return _redact_event({
        "text": visible,
        "stdout": stdout,
        "session_id": session_id,
        "model": chosen,
        "agent": agent_name,
        "cwd": workdir,
    })


def _version_text() -> str:
    env = os.environ.copy()
    env["OPENCODE_DISABLE_AUTOUPDATE"] = "true"
    result = _run(["opencode", "--version"], cwd=str(MODULE_CONFIG.parent), timeout=30, env=env)
    return _require_ok(result, "opencode --version").strip()


def _healthy(port: int) -> bool:
    url = f"http://127.0.0.1:{port}/global/health"
    request = urllib.request.Request(url)
    password = os.environ.get("OPENCODE_SERVER_PASSWORD", "")
    if password:
        username = os.environ.get("OPENCODE_SERVER_USERNAME", "opencode")
        value = base64.b64encode(f"{username}:{password}".encode()).decode()
        request.add_header("Authorization", f"Basic {value}")
    try:
        # Local service probes must not be sent to an environment HTTP proxy.
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request, timeout=1) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return False
    return isinstance(body, dict) and body.get("healthy") is True and body.get("version") == PINNED_VERSION


def _owned_serve_alive() -> bool:
    """Only the Popen child created by this interpreter can authorize a signal.

    PID/state files cannot prove ownership, and are deliberately never read.
    poll() reaps an exited child before it could be mistaken for a reused PID.
    """
    proc = _SERVE_PROCESS
    return (proc is not None and _SERVE_OWNER_PID == os.getpid()
            and proc.poll() is None)


def _serve_status() -> dict[str, object]:
    with _SERVE_LOCK:
        alive = _owned_serve_alive()
        healthy = _healthy(_SERVE_PORT) if alive else False
        return {
            "running": alive and healthy,
            "port": _SERVE_PORT if alive else 0,
            "hostname": _SERVE_HOST if alive else "",
            "pid": _SERVE_PROCESS.pid if alive else 0,
            "healthy": healthy,
            "version": PINNED_VERSION if healthy else "",
        }


def _signal_owned_serve(sig: int) -> None:
    proc = _SERVE_PROCESS
    if not _owned_serve_alive():
        return
    # start_new_session makes the owned child its own group leader. Never
    # signal a mismatching group or fall back to a PID from external state.
    try:
        if os.getpgid(proc.pid) != proc.pid:
            raise RuntimeError("opencode serve process identity mismatch; signal refused")
        os.killpg(proc.pid, sig)
    except ProcessLookupError:
        pass


def _stop_serve() -> None:
    global _SERVE_PROCESS, _SERVE_PORT, _SERVE_HOST, _SERVE_OWNER_PID
    with _SERVE_LOCK:
        proc = _SERVE_PROCESS
        if proc is None:
            return
        if _SERVE_OWNER_PID != os.getpid():
            raise RuntimeError("opencode serve is owned by another interpreter; signal refused")
        if proc.poll() is None:
            _signal_owned_serve(signal.SIGTERM)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                _signal_owned_serve(signal.SIGKILL)
                proc.wait(timeout=5)
        _SERVE_PROCESS = None
        _SERVE_PORT = 0
        _SERVE_HOST = ""
        _SERVE_OWNER_PID = 0


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
    description="Compatibility alias of opencode_run. Returns sanitized JSON-event stdout.",
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
        raise RuntimeError(f"opencode version does not match pin {PINNED_VERSION}")
    return found


@command("opencode_setup_check", description="Check the opencode binary and DashScope config.")
def opencode_setup_check() -> str:
    """Return ``ok`` when the pin and ``opencode.json`` match this template."""
    _check_state_permissions()
    found = _version_text()
    if found != PINNED_VERSION:
        raise RuntimeError(f"opencode version does not match pin {PINNED_VERSION}")
    _assert_dashscope(_load_config(_config_file()))
    return "ok"


def _check_state_permissions() -> None:
    """Inspect native writable state without creating or reading its contents."""
    data = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "opencode"
    for target in (data / "log", data / "log" / "opencode.log"):
        while not target.exists():
            target = target.parent
        if not os.access(target, os.W_OK):
            raise RuntimeError("OpenCode data/log state is not writable by the runtime user; rebuild with corrected ownership")


@command("opencode_serve_start", description="Start opencode serve and wait until it is healthy.")
def opencode_serve_start(port: int = 4096, hostname: str = "0.0.0.0") -> dict[str, object]:
    """Bind ``opencode serve`` and return when ``/global/health`` is healthy."""
    with _SERVE_LOCK:
        return _start_serve(port, hostname)


def _start_serve(port: int, hostname: str) -> dict[str, object]:
    global _SERVE_PROCESS, _SERVE_PORT, _SERVE_HOST, _SERVE_OWNER_PID
    if port < 1 or port > 65535:
        raise ValueError("port must be between 1 and 65535")
    host = hostname.strip()
    if not host:
        raise ValueError("hostname is required")
    current = _serve_status()
    if current["running"]:
        if int(current["port"]) != port or current["hostname"] != host:
            raise RuntimeError("opencode serve is already running with different bind settings")
        return current
    _stop_serve()
    config_path = str(_config_file())
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
    try:
        proc = subprocess.Popen(
            argv,
            cwd=_workdir(""),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("opencode CLI was not found on PATH") from exc
    _SERVE_PROCESS = proc
    _SERVE_PORT = port
    _SERVE_HOST = host
    _SERVE_OWNER_PID = os.getpid()
    deadline = time.monotonic() + SERVE_READY_S
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            code = proc.returncode
            _stop_serve()
            raise RuntimeError(f"opencode serve exited {code}; CLI output omitted")
        if _healthy(port):
            return _serve_status()
        time.sleep(0.2)
    _stop_serve()
    raise RuntimeError(f"opencode serve did not become healthy on port {port}")


@command("opencode_serve_status", description="Report whether opencode serve is healthy.")
def opencode_serve_status() -> dict[str, object]:
    """Report this interpreter's owned child plus its local health probe."""
    return _serve_status()


@command("opencode_serve_stop", description="Stop opencode serve if this template started it.")
def opencode_serve_stop() -> str:
    """Terminate the serve process group. Does nothing when it is already stopped."""
    _stop_serve()
    return "stopped"


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
