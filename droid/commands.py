"""Bounded, non-interactive Factory Droid commands. No credentials are returned."""
from __future__ import annotations

import json
import importlib.util
import tempfile
import os
from pathlib import Path
import shutil

from agent_sandbox.server import command, start

PACKAGE = "@factory/cli"
PINNED_VERSION = "0.241.1"

_BYOK_SPEC = importlib.util.spec_from_file_location("droid_explicit_byok", Path(__file__).with_name("byok.py"))
_BYOK = importlib.util.module_from_spec(_BYOK_SPEC)
_BYOK_SPEC.loader.exec_module(_BYOK)


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
    if not isinstance(cwd, str) or len(cwd.encode()) > 4096 or "\0" in cwd:
        raise ValueError("cwd must be a bounded workspace path")
    root = _workspace()
    path = (root / cwd).resolve() if cwd else root
    if not path.is_relative_to(root) or not path.is_dir():
        raise ValueError("cwd must be an existing directory inside WORKSPACE")
    return path


def _executable() -> str:
    return _BYOK.binary()


def _run_process(argv: list[str], *, cwd: str, timeout: int | float,
                 env: dict | None = None, input_text: str | None = None) -> tuple[int, str, str]:
    """Bounded identity-pinned process; preserve existing helper signature."""
    if env is None:
        env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": str(cwd), "LANG": "C.UTF-8"}
    try:
        if input_text is None:
            return _BYOK.process.run(argv, cwd=cwd, timeout=timeout, env=env)
        descriptor = os.memfd_create("droid-input", os.MFD_CLOEXEC)
        with os.fdopen(descriptor, "w+b") as stream:
            stream.write(input_text.encode()); stream.seek(0)
            return _BYOK.process.run(argv, cwd=cwd, timeout=timeout, env=env, input_file=stream)
    except RuntimeError as exc:
        if "exceeded timeout_s" in str(exc):
            raise RuntimeError(f"droid timed out after {timeout} seconds") from None
        raise


def _run(args: list[str], cwd: Path, timeout: int) -> str:
    try:
        with tempfile.TemporaryDirectory(prefix="abx-droid-legacy-home-") as value:
            env = _BYOK.environment(Path(value), model=False)
            if os.environ.get("FACTORY_API_KEY"):
                env["FACTORY_API_KEY"] = os.environ["FACTORY_API_KEY"]
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
    try:
        _BYOK.binary()
        installed = True
    except RuntimeError:
        installed = False
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
    if not isinstance(prompt, str) or not prompt.strip() or "\0" in prompt or len(prompt.encode()) > 32768:
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
