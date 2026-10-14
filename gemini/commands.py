"""gemini — Gemini CLI headless command.

The named command runs ``gemini`` from npm package ``@google/gemini-cli``.
Headless mode is ``-p`` / ``--prompt``. ``--yolo`` only auto-approves tool
calls; it does not select headless mode. The prompt is one argv element and
is not interpolated into a shell string.

``GEMINI_API_KEY`` is required when the command is invoked. This module does
not call the CLI at import or at server start.
"""
from __future__ import annotations

import os
import subprocess

from agent_sandbox.server import command, start

# @google/gemini-cli@0.64.0 DEFAULT_GEMINI_FLASH_LITE_MODEL.
DEFAULT_MODEL = "gemini-3.1-flash-lite"


def _resolved_model(model: str) -> str:
    chosen = (model or os.environ.get("GEMINI_MODEL") or DEFAULT_MODEL).strip()
    return chosen or DEFAULT_MODEL


@command("gemini", description="Run Gemini CLI headless (gemini -p).")
def gemini(prompt: str, model: str = "") -> str:
    """Run ``gemini -p <prompt> --yolo --model <model>``.

    ``<model>`` is *model*, else ``GEMINI_MODEL``, else ``gemini-3.1-flash-lite``.
    """
    if not os.environ.get("GEMINI_API_KEY", "").strip():
        raise RuntimeError("GEMINI_API_KEY is required to run gemini")

    text = prompt.strip()
    if not text:
        raise ValueError("prompt is required")

    chosen = _resolved_model(model)
    argv = ["gemini", "-p", text, "--yolo", "--model", chosen]
    workdir = "/app" if os.path.isdir("/app") else None
    try:
        result = subprocess.run(
            argv,
            cwd=workdir,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("gemini CLI was not found on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("gemini -p timed out after 600 seconds") from exc

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(detail or f"gemini exited {result.returncode}")
    return result.stdout


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
