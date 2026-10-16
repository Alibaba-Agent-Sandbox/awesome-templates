"""Named commands for the OpenAI Codex CLI (@openai/codex).

``agent-sandbox-server serve --commands`` imports this module. ``start()``
runs only under ``python3 commands.py``.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from agent_sandbox.server import command, start

PINNED_VERSION = "0.162.1"
BYPASS_FLAG = "--dangerously-bypass-approvals-and-sandbox"
SANDBOX_MODES = ("read-only", "workspace-write", "danger-full-access")
SANDBOX_CHOICES = ("auto", "bypass", *SANDBOX_MODES)
APPROVAL_POLICIES = ("untrusted", "on-request", "never")
RESERVED_PROVIDERS = ("openai", "ollama", "lmstudio")
_PROBE: dict | None = None


def _redact(text: str) -> str:
    redacted = text
    for key, value in os.environ.items():
        if not value:
            continue
        if re.search(r"(KEY|SECRET|TOKEN|PASSWORD|CREDENTIAL)", key, re.IGNORECASE):
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


def _codex_home() -> Path:
    raw = os.environ.get("CODEX_HOME", "").strip()
    if raw:
        return Path(raw).expanduser()
    return Path.home() / ".codex"


def _workspace() -> Path:
    raw = os.environ.get("WORKSPACE", "").strip()
    if raw:
        return Path(raw).expanduser()
    return Path("/home/user/workspace")


def _which_codex() -> str:
    return shutil.which("codex") or ""


def _find_bwrap() -> str:
    found = shutil.which("bwrap") or ""
    if found:
        return found
    patterns = (
        "/usr/local/lib/node_modules/@openai/codex-linux-*/vendor/*/codex-resources/bwrap",
        "/usr/lib/node_modules/@openai/codex-linux-*/vendor/*/codex-resources/bwrap",
    )
    import glob

    for pattern in patterns:
        hits = sorted(glob.glob(pattern))
        for hit in hits:
            if os.access(hit, os.X_OK):
                return hit
    return ""


def _key_present(name: str) -> bool:
    return bool(os.environ.get(name, "").strip())


def _toml_string(value: str) -> str:
    if "\n" in value or "\r" in value:
        raise ValueError("config values must be a single line")
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _validate_identifier(value: str, label: str) -> str:
    text = value.strip()
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", text):
        raise ValueError(f"{label} must be an identifier")
    return text


def _base_url_from_env() -> tuple[str, str]:
    """Return (url, source env name). Empty url when neither variable is set."""
    for name in ("ABX_LLM_BASE_URL", "OPENAI_BASE_URL"):
        value = os.environ.get(name, "").strip()
        if value:
            return value, name
    return "", ""


def _env_key_from_env(base_source: str) -> str:
    for name in ("ABX_LLM_API_KEY", "OPENAI_API_KEY", "CODEX_API_KEY"):
        if _key_present(name):
            return name
    if base_source == "ABX_LLM_BASE_URL":
        return "ABX_LLM_API_KEY"
    if base_source == "OPENAI_BASE_URL":
        return "OPENAI_API_KEY"
    return "OPENAI_API_KEY"


def _model_from_env() -> str:
    for name in ("CODEX_MODEL", "ABX_LLM_MODEL"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


def _probe_bwrap(path: str) -> tuple[bool, str]:
    if not path:
        return False, ""
    try:
        proc = subprocess.run(
            [path, "--unshare-user", "--die-with-parent", "--ro-bind", "/", "/", "--", "true"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, _redact(str(exc))[:400]
    if proc.returncode == 0:
        return True, ""
    detail = (proc.stderr or proc.stdout or f"exit {proc.returncode}").strip()
    return False, _redact(detail)[:400]


def sandbox_status(*, refresh: bool = False) -> dict:
    """Probe Codex's Linux sandbox once per process.

    Express runs as non-root without capabilities. Bubblewrap user namespaces
    (and the legacy landlock path) then fail. The documented bypass is
    ``--dangerously-bypass-approvals-and-sandbox``.
    """
    global _PROBE
    if _PROBE is not None and not refresh:
        return _PROBE

    binary = _which_codex()
    bwrap = _find_bwrap()
    bwrap_ok, bwrap_error = _probe_bwrap(bwrap)
    landlock = Path("/sys/kernel/security/landlock").exists()
    probe_cmd = [
        binary or "codex",
        "sandbox",
        "--permission-profile",
        ":read-only",
        "--",
        "true",
    ]
    linux_sandbox = False
    sandbox_error = ""
    if not binary:
        sandbox_error = "codex is not on PATH"
    else:
        probe_home = _codex_home() / "sandbox-probe"
        probe_home.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env["CODEX_HOME"] = str(probe_home)
        try:
            proc = subprocess.run(
                [binary, "sandbox", "--permission-profile", ":read-only", "--", "true"],
                capture_output=True,
                text=True,
                timeout=20,
                env=env,
                stdin=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired:
            sandbox_error = "codex sandbox probe timed out"
        except OSError as exc:
            sandbox_error = _redact(str(exc))[:400]
        else:
            linux_sandbox = proc.returncode == 0
            if not linux_sandbox:
                sandbox_error = _redact((proc.stderr or proc.stdout or f"exit {proc.returncode}").strip())[:400]

    version = ""
    if binary:
        try:
            proc = subprocess.run(
                [binary, "--version"],
                capture_output=True,
                text=True,
                timeout=20,
                stdin=subprocess.DEVNULL,
            )
            match = re.search(r"\d+\.\d+\.\d+", (proc.stdout or "") + (proc.stderr or ""))
            if proc.returncode == 0 and match:
                version = match.group(0)
        except (OSError, subprocess.TimeoutExpired):
            version = ""

    use_bypass = bool(binary) and not linux_sandbox
    status = {
        "binary_present": bool(binary),
        "binary": binary,
        "version": version,
        "pinned_version": PINNED_VERSION,
        "version_matches_pin": version == PINNED_VERSION,
        "linux_sandbox": linux_sandbox,
        "sandbox_probe": " ".join(probe_cmd),
        "sandbox_error": sandbox_error,
        "bwrap_path": bwrap,
        "bwrap_userns": bwrap_ok if bwrap else False,
        "bwrap_error": bwrap_error,
        "landlock_sysfs": landlock,
        "bypass_flag": BYPASS_FLAG,
        "use_bypass": use_bypass,
        "recommended_sandbox": "bypass" if use_bypass else ("workspace-write" if binary else ""),
    }
    _PROBE = status
    return status


def _resolve_cwd(cwd: str) -> Path:
    raw = cwd.strip()
    if not raw:
        path = _workspace()
    else:
        candidate = Path(raw).expanduser()
        path = candidate if candidate.is_absolute() else _workspace() / candidate
    path.mkdir(parents=True, exist_ok=True)
    if not path.is_dir():
        raise ValueError(f"cwd is not a directory: {path}")
    return path


def _ensure_git(cwd: Path) -> None:
    """Init a repo only when ``cwd`` is not already inside one.

    A nested ``git init`` in the template directory would break the catalog checkout.
    """
    git = shutil.which("git")
    if not git:
        return
    if (cwd / ".git").exists():
        return
    inside = subprocess.run(
        [git, "rev-parse", "--is-inside-work-tree"],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if inside.returncode == 0 and inside.stdout.strip() == "true":
        return
    subprocess.run(
        [git, "init"],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )


def _render_config(*, provider: str, base_url: str, env_key: str, model: str) -> str:
    provider_id = _validate_identifier(provider, "provider")
    if provider_id in RESERVED_PROVIDERS:
        raise ValueError(
            f"provider {provider_id!r} is reserved by Codex; use another id such as 'compatible'"
        )
    key_name = _validate_identifier(env_key, "env_key")
    url = base_url.strip()
    if not url.startswith(("https://", "http://")):
        raise ValueError("base_url must start with http:// or https://")
    lines = [f"model_provider = {_toml_string(provider_id)}"]
    model_name = model.strip()
    if model_name:
        lines.append(f"model = {_toml_string(model_name)}")
    lines.extend(
        [
            "",
            f"[model_providers.{provider_id}]",
            f"name = {_toml_string('OpenAI-compatible')}",
            f"base_url = {_toml_string(url)}",
            f"env_key = {_toml_string(key_name)}",
            'wire_api = "responses"',
            "supports_websockets = false",
            "",
        ]
    )
    return "\n".join(lines)


def _write_config_text(home: Path, text: str) -> Path:
    home.mkdir(parents=True, exist_ok=True)
    path = home / "config.toml"
    path.write_text(text, encoding="utf-8")
    os.chmod(path, 0o600)
    return path


def _ensure_provider_config() -> dict | None:
    url, source = _base_url_from_env()
    if not url:
        return None
    home = _codex_home()
    path = home / "config.toml"
    if path.is_file():
        return None
    text = _render_config(
        provider="compatible",
        base_url=url,
        env_key=_env_key_from_env(source),
        model=_model_from_env(),
    )
    written = _write_config_text(home, text)
    return {"path": str(written), "source": source}


def _apply_sandbox(requested: str) -> tuple[bool, str]:
    """Return (bypass, applied mode).

    Only ``auto`` may fall back to the container's isolation boundary.
    An explicit mode must never silently lose its sandbox or approval policy.
    """
    mode = requested.strip() or "auto"
    if mode not in SANDBOX_CHOICES:
        raise ValueError(f"sandbox must be one of: {', '.join(SANDBOX_CHOICES)}")
    status = sandbox_status()
    if not status["binary_present"]:
        raise RuntimeError("codex is not on PATH")
    if mode == "bypass" or (mode == "auto" and status["use_bypass"]):
        return True, "bypass"
    if mode in SANDBOX_MODES and not status["linux_sandbox"]:
        raise RuntimeError(
            f"Codex Linux sandbox is unavailable; cannot honor sandbox={mode!r}. "
            "Use sandbox='auto' or sandbox='bypass' only when the container's "
            "isolation is sufficient."
        )
    applied = "workspace-write" if mode == "auto" else mode
    return False, applied


def _parse_events(stdout: str) -> list[dict]:
    events: list[dict] = []
    for line in stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return events


def _last_message(events: list[dict]) -> str:
    text = ""
    for event in events:
        item = event.get("item")
        if not isinstance(item, dict):
            continue
        if item.get("type") != "agent_message":
            continue
        value = item.get("text")
        if isinstance(value, str):
            text = value
    return text


def _thread_id(events: list[dict]) -> str:
    for event in events:
        if event.get("type") == "thread.started" and isinstance(event.get("thread_id"), str):
            return event["thread_id"]
    return ""


def _failure_message(events: list[dict]) -> str:
    for event in reversed(events):
        if event.get("type") == "error" and isinstance(event.get("message"), str):
            return event["message"]
        error = event.get("error")
        if isinstance(error, dict) and isinstance(error.get("message"), str):
            return error["message"]
        item = event.get("item")
        if isinstance(item, dict) and item.get("type") == "error" and isinstance(item.get("message"), str):
            return item["message"]
    return ""


def _cap_events(events: list[dict]) -> tuple[list[dict], bool]:
    if len(events) <= 200:
        return events, False
    return events[:1] + events[-199:], True


def _build_argv(
    *,
    prompt: str,
    model: str,
    cwd: Path,
    bypass: bool,
    applied: str,
    approval: str,
    json_events: bool,
    resume: str,
    resume_all: bool,
    skip_git_repo_check: bool,
    ephemeral: bool,
    output_schema: str,
) -> list[str]:
    binary = _which_codex()
    argv = [binary, "exec", "--color", "never"]
    if json_events:
        argv.append("--json")
    if skip_git_repo_check:
        argv.append("--skip-git-repo-check")
    if ephemeral:
        argv.append("--ephemeral")
    if model.strip():
        argv.extend(["--model", model.strip()])
    argv.extend(["-C", str(cwd)])
    if output_schema.strip():
        schema = Path(output_schema).expanduser()
        if not schema.is_file():
            raise ValueError(f"output_schema is not a file: {schema}")
        argv.extend(["--output-schema", str(schema)])
    if bypass:
        argv.append(BYPASS_FLAG)
    else:
        argv.extend(["--sandbox", applied])
        if approval:
            argv.extend(["-c", f'approval_policy="{approval}"'])
    if resume == "last":
        argv.append("resume")
        argv.append("--last")
        if resume_all:
            argv.append("--all")
    elif resume:
        argv.extend(["resume", resume])
    elif resume_all:
        raise ValueError("resume_all requires resume='last'")
    argv.append("--")
    argv.append(prompt)
    return argv


def _run_codex(argv: list[str], timeout_s: int) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["CODEX_HOME"] = str(_codex_home())
    custom = _base_url_from_env()[0] or (_codex_home() / "config.toml").is_file()
    if not custom and not env.get("CODEX_API_KEY") and env.get("OPENAI_API_KEY"):
        env["CODEX_API_KEY"] = env["OPENAI_API_KEY"]
    try:
        return subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=env,
            stdin=subprocess.DEVNULL,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stderr = exc.stderr or ""
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")
        raise RuntimeError(f"codex exec timed out after {timeout_s}s: {_redact(stderr)[-500:]}") from None


@command("codex_version", description="Print the installed Codex CLI version.")
def codex_version() -> str:
    """Return the ``X.Y.Z`` token from ``codex --version``."""
    binary = _which_codex()
    if not binary:
        raise RuntimeError("codex is not on PATH")
    proc = subprocess.run(
        [binary, "--version"],
        capture_output=True,
        text=True,
        timeout=30,
        stdin=subprocess.DEVNULL,
        check=False,
    )
    text = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        raise RuntimeError(_redact(text.strip())[:500] or "codex --version failed")
    match = re.search(r"\d+\.\d+\.\d+", text)
    if not match:
        raise RuntimeError(f"could not parse codex version from {text.strip()[:200]}")
    return match.group(0)


@command(
    "codex_setup_check",
    description="Report the Codex binary, Linux sandbox probe, and the Express bypass flag.",
)
def codex_setup_check() -> dict:
    """Probe the CLI without calling a model."""
    status = sandbox_status()
    cwd = _workspace()
    agents = cwd / "AGENTS.md"
    config = _codex_home() / "config.toml"
    reported = dict(status)
    reported["agents_md"] = str(agents) if agents.is_file() else ""
    reported["workspace"] = str(cwd)
    reported["config_path"] = str(config)
    reported["config_present"] = config.is_file()
    reported["api_key_present"] = {
        "ABX_LLM_API_KEY": _key_present("ABX_LLM_API_KEY"),
        "OPENAI_API_KEY": _key_present("OPENAI_API_KEY"),
        "CODEX_API_KEY": _key_present("CODEX_API_KEY"),
    }
    reported["base_url_present"] = {
        "ABX_LLM_BASE_URL": _key_present("ABX_LLM_BASE_URL"),
        "OPENAI_BASE_URL": _key_present("OPENAI_BASE_URL"),
    }
    reported["full_auto_supported"] = False
    return reported


@command(
    "codex_config_write",
    description="Write $CODEX_HOME/config.toml for an OpenAI-compatible provider.",
)
def codex_config_write(
    base_url: str = "",
    provider: str = "compatible",
    env_key: str = "",
    model: str = "",
    wire_api: str = "responses",
    codex_home: str = "",
) -> dict:
    """Write a user-level Codex config. The API key stays in the environment."""
    if wire_api.strip() != "responses":
        raise ValueError(
            'wire_api "chat" is no longer supported by Codex; set wire_api = "responses"'
        )
    url = base_url.strip()
    source = ""
    if not url:
        url, source = _base_url_from_env()
    if not url:
        raise ValueError("base_url is required (or set ABX_LLM_BASE_URL / OPENAI_BASE_URL)")
    key_name = env_key.strip() or _env_key_from_env(source)
    model_name = model.strip() or _model_from_env()
    text = _render_config(provider=provider, base_url=url, env_key=key_name, model=model_name)
    home = Path(codex_home).expanduser() if codex_home.strip() else _codex_home()
    path = _write_config_text(home, text)
    return {
        "path": str(path),
        "provider": provider.strip() or "compatible",
        "base_url": url,
        "env_key": key_name,
        "model": model_name,
        "wire_api": "responses",
        "supports_websockets": False,
        "toml": text,
    }


@command("codex_agents_write", description="Write AGENTS.md into the workspace Codex will read.")
def codex_agents_write(content: str, cwd: str = "") -> dict:
    """Codex loads ``AGENTS.md`` from the working directory. This does not call the model."""
    if not content.strip():
        raise ValueError("content is required")
    if len(content.encode("utf-8")) > 200_000:
        raise ValueError("content is larger than 200000 bytes")
    path = _resolve_cwd(cwd) / "AGENTS.md"
    path.write_text(content, encoding="utf-8")
    return {"path": str(path), "bytes": path.stat().st_size}


@command(
    "codex_exec",
    description="Run non-interactive `codex exec` and return JSON events.",
)
def codex_exec(
    prompt: str,
    model: str = "",
    cwd: str = "",
    sandbox: str = "auto",
    approval: str = "never",
    json_events: bool = True,
    resume: str = "",
    resume_all: bool = False,
    skip_git_repo_check: bool = True,
    ephemeral: bool = False,
    output_schema: str = "",
    agents_md: str = "",
    timeout_s: int = 300,
) -> dict:
    """Run ``codex exec``. A non-zero exit raises ``RuntimeError``."""
    text = prompt.strip()
    if not text:
        raise ValueError("prompt is required")
    if timeout_s < 1 or timeout_s > 3600:
        raise ValueError("timeout_s must be between 1 and 3600")
    policy = approval.strip()
    if policy and policy not in APPROVAL_POLICIES:
        raise ValueError(f"approval must be one of: {', '.join(APPROVAL_POLICIES)}")
    requested = sandbox.strip() or "auto"
    if requested not in SANDBOX_CHOICES:
        raise ValueError(f"sandbox must be one of: {', '.join(SANDBOX_CHOICES)}")
    resume_id = resume.strip()
    if resume_all and resume_id != "last":
        raise ValueError("resume_all requires resume='last'")
    bypass, applied = _apply_sandbox(requested)
    directory = _resolve_cwd(cwd)
    _ensure_git(directory)
    if agents_md.strip():
        codex_agents_write(agents_md, cwd=str(directory))
    _ensure_provider_config()
    argv = _build_argv(
        prompt=text,
        model=model,
        cwd=directory,
        bypass=bypass,
        applied=applied,
        approval=policy,
        json_events=json_events,
        resume=resume_id,
        resume_all=resume_all,
        skip_git_repo_check=skip_git_repo_check,
        ephemeral=ephemeral,
        output_schema=output_schema,
    )
    proc = _run_codex(argv, timeout_s)
    # Tool events can contain model-generated shell output, including environment
    # values. Apply the same redaction as stderr before returning any events.
    stdout = _redact(proc.stdout or "")
    events = [_redact_event(event) for event in _parse_events(proc.stdout or "")]
    message = _last_message(events) if json_events else stdout.strip()
    if not message and not json_events:
        message = stdout.strip()
    failure = _failure_message(events)
    stderr = _redact((proc.stderr or "").strip())[-4000:]
    if proc.returncode != 0 or any(event.get("type") == "turn.failed" for event in events):
        detail = failure or stderr or f"exit {proc.returncode}"
        raise RuntimeError(_redact(detail)[:800])
    kept, truncated = _cap_events(events)
    return {
        "thread_id": _thread_id(events),
        "last_message": message,
        "events": kept,
        "event_count": len(events),
        "events_truncated": truncated,
        "sandbox_requested": sandbox.strip() or "auto",
        "sandbox_applied": applied,
        "bypass": bypass,
        "argv": [_redact(arg) for arg in argv],
        "stderr": stderr,
    }


@command("codex", description="Compatibility alias of codex_exec (prompt and model only).")
def codex(prompt: str, model: str = "") -> dict:
    """The legacy ``codex -p`` argv is not accepted by Codex 0.162.1."""
    return codex_exec(prompt=prompt, model=model)


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
