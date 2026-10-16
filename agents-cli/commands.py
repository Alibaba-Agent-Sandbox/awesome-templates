"""Pinned Codex/Qwen Agents API with an explicit endpoint allowlist.

Synthetic CLIs belong to protocol tests and are never selected here.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

from agent_sandbox.server import ServerPolicy, command, start

_HERE = Path(__file__).resolve().parent
POLICY = ServerPolicy.from_file(str(_HERE / "server-policy.json"))
VERSIONS = {"codex": "0.162.1", "qwen": "0.23.0"}


@command("agents_version", description="Check both pinned CLI versions without a model call.")
def agents_version() -> str:
    for binary, expected in VERSIONS.items():
        executable = shutil.which(binary)
        if executable is None:
            raise RuntimeError(f"{binary} is missing; rebuild the pinned template")
        try:
            result = subprocess.run([executable, "--version"], capture_output=True,
                                    text=True, timeout=20, check=False)
        except (OSError, subprocess.TimeoutExpired):
            raise RuntimeError(f"{binary} version check failed") from None
        # Raw CLI output can contain local paths or credentials.
        if result.returncode != 0 or result.stdout.strip() not in {expected, f"codex-cli {expected}"}:
            raise RuntimeError(f"{binary} version does not match the template pin")
    return "codex 0.162.1; qwen-code 0.23.0"


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")), policy=POLICY)
