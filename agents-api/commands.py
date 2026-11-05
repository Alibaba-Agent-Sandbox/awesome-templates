"""Local version diagnostics; the managed guest does not expose command routes."""
from __future__ import annotations

import os
import shutil
import subprocess

from agent_sandbox.server import command, start


@command("agents_version", description="Check pinned CLI versions locally without calling a model.")
def agents_version() -> str:
    for binary, expected in (("codex", "0.162.1"), ("qwen", "0.23.0")):
        executable = shutil.which(binary)
        if executable is None:
            raise RuntimeError("A pinned Agent CLI is unavailable")
        try:
            result = subprocess.run([executable, "--version"], capture_output=True, text=True, timeout=20, check=False)
        except (OSError, subprocess.TimeoutExpired):
            raise RuntimeError("An Agent CLI version check failed") from None
        if result.returncode or result.stdout.strip() not in {expected, "codex-cli " + expected}:
            raise RuntimeError("An Agent CLI does not match its template version")
    return "codex 0.162.1; qwen-code 0.23.0"


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
