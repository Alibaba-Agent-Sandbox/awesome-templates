"""opencode — OpenCode coding agent command.

The named command runs the real CLI (``opencode`` from npm package
``opencode-ai``). The prompt is copied into the child environment as
``OPENCODE_PROMPT`` and passed as one argv element. It is not interpolated
into a shell string.

``OPENCODE_API_KEY`` is the credential the OpenCode Zen provider reads
(provider id ``opencode``). This module does not call the CLI at import or
at server start. The CLI runs only when a caller invokes the ``opencode``
command. An empty key does not skip that call: the documented free model
may answer, and a failure that asks for a key raises ``RuntimeError``
naming ``OPENCODE_API_KEY``.
"""
from __future__ import annotations

import os
import subprocess

from agent_sandbox.server import command, start

# Verified in opencode-ai 1.19.0 and on https://opencode.ai/docs/zen/ :
# provider ``opencode`` lists model id ``big-pickle`` at cost 0.
# Selector form is provider/model. OpenSandbox's older default
# ``opencode/deepseek-v4-flash-free`` is a finished promotion.
DEFAULT_MODEL = "opencode/big-pickle"
PROMPT_ENV = "OPENCODE_PROMPT"
_KEY_MARKERS = (
    "opencode_api_key",
    "api key",
    "api_key",
    "apikey",
    "no credentials",
    "missing credential",
    "unauthorized",
    "authentication",
    "not authenticated",
    "auth required",
    "invalid key",
)


def _resolved_model(model: str) -> str:
    """Command argument, then ``OPENCODE_MODEL``, then the documented free model."""
    chosen = (model or os.environ.get("OPENCODE_MODEL") or DEFAULT_MODEL).strip()
    return chosen or DEFAULT_MODEL


def _key_set() -> bool:
    return bool(os.environ.get("OPENCODE_API_KEY", "").strip())


def _needs_api_key(detail: str) -> bool:
    lowered = detail.lower()
    return any(marker in lowered for marker in _KEY_MARKERS)


@command("opencode", description="Run OpenCode non-interactively (opencode run).")
def opencode(prompt: str, model: str = "") -> str:
    """Run ``opencode run --format json --auto --model <model> <prompt>``.

    ``<prompt>`` is the value of ``OPENCODE_PROMPT`` in the child process.
    ``<model>`` is *model*, else ``OPENCODE_MODEL``, else ``opencode/big-pickle``.
    """
    text = prompt.strip()
    if not text:
        raise ValueError("prompt is required")

    chosen = _resolved_model(model)
    env = os.environ.copy()
    env[PROMPT_ENV] = text
    env["OPENCODE_MODEL"] = chosen
    env.setdefault("OPENCODE_DISABLE_AUTOUPDATE", "true")
    if not env.get("OPENCODE_API_KEY", "").strip():
        env.pop("OPENCODE_API_KEY", None)

    # Argv, not a shell. The prompt is read back from the environment.
    argv = [
        "opencode",
        "run",
        "--format",
        "json",
        "--auto",
        "--model",
        chosen,
        env[PROMPT_ENV],
    ]
    workdir = "/app" if os.path.isdir("/app") else None
    try:
        result = subprocess.run(
            argv,
            cwd=workdir,
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("opencode CLI was not found on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("opencode run timed out after 600 seconds") from exc

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        if not _key_set() and _needs_api_key(detail):
            message = "OPENCODE_API_KEY is required for this OpenCode model"
            if detail:
                message = f"{message}: {detail}"
            raise RuntimeError(message)
        raise RuntimeError(detail or f"opencode exited {result.returncode}")
    return result.stdout


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
