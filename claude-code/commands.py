"""Claude Code named commands. Prompts are passed as argv, never shell text."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
import subprocess

from agent_sandbox.server import command, start
import importlib.util
_spec=importlib.util.spec_from_file_location("owned_claude_byok",Path(__file__).with_name("byok.py"))
_BYOK=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_BYOK)


CLAUDE_VERSION = "2.0.76"


def _redact_result(value):
    if isinstance(value, str):
        for name, secret in os.environ.items():
            if secret and re.search(r"KEY|SECRET|TOKEN|PASSWORD", name, re.IGNORECASE):
                value = value.replace(secret, "***")
        return value
    if isinstance(value, list):
        return [_redact_result(item) for item in value]
    if isinstance(value, dict):
        return {_redact_result(key): _redact_result(item) for key, item in value.items()}
    return value


def _workspace(cwd: str) -> str:
    root = Path(os.environ.get("WORKSPACE", "/home/user/app")).resolve()
    target = (root / cwd).resolve() if cwd else root
    if not target.is_relative_to(root) or not target.is_dir():
        raise ValueError("cwd must be an existing directory inside WORKSPACE")
    return str(target)


def _run(argv: list[str], *, cwd: str, timeout: int) -> str:
    try:
        result = subprocess.run(
            argv, cwd=cwd, capture_output=True, text=True, timeout=timeout,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("Claude Code timed out") from None
    except OSError:
        raise RuntimeError("Claude Code could not be started") from None
    if result.returncode != 0:
        # Upstream diagnostics can include headers, prompts or credential values.
        raise RuntimeError(f"Claude Code exited with status {result.returncode}")
    return result.stdout


@command("claude_version", description="Return the installed Claude Code CLI version (no model call).")
def claude_version() -> str:
    return _run(["claude", "--version"], cwd=_workspace(""), timeout=15).strip()


@command("claude", description="Run Claude Code with explicit non-interactive tool permissions.")
def claude(
    prompt: str,
    model: str = "sonnet",
    cwd: str = "",
    allowed_tools: str = "Read,Edit,Write",
    resume: str = "",
    command_timeout: int = 300,
) -> str:
    """Return Claude's JSON output as a string; collect workspace files separately."""
    if not prompt.strip():
        raise ValueError("prompt must not be empty")
    if command_timeout < 1 or command_timeout > 900:
        raise ValueError("command_timeout must be between 1 and 900 seconds")
    argv = [
        "claude", "-p", prompt, "--model", model, "--output-format", "json",
        "--permission-mode", "dontAsk", "--allowedTools", allowed_tools,
    ]
    if resume:
        argv.extend(["--resume", resume])
    output = _run(argv, cwd=_workspace(cwd), timeout=command_timeout)
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError:
        raise RuntimeError("Claude Code returned invalid JSON") from None
    if not isinstance(parsed, dict) or parsed.get("is_error") is True:
        raise RuntimeError("Claude Code reported an unsuccessful result")
    return json.dumps(_redact_result(parsed), ensure_ascii=False)


@command("claude_setup_check", description="Read-only explicit compatible-model configuration presence; no values or authentication.")
def claude_setup_check() -> dict:
    return _BYOK.setup()


@command("claude_native_check", description="Original hash-pinned Claude CLI headless flags without a model call.")
def claude_native_check() -> dict:
    text=_BYOK.diagnostic(["--help"])
    return {"original_native":True,"isolated_settings":"--setting-sources"in text,"no_session_persistence":"--no-session-persistence"in text,"strict_mcp":"--strict-mcp-config"in text}


@command("claude_byok", description="Original Claude Code using explicit authored Messages-to-Chat text/tool adapter and bounded owned per-call state.")
def claude_byok(prompt: str, cwd: str="", command_timeout: int=300, allow_unsafe_tools: bool=False) -> dict:
    return _BYOK.run(prompt,cwd,command_timeout,allow_unsafe_tools)


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
