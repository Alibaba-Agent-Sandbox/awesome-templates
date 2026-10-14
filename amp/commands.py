"""amp — Sourcegraph Amp 编码 CLI 沙箱命令。"""
from __future__ import annotations

import os

from agent_sandbox.server import command, start


@command("amp", description="Run the Amp coding agent with a prompt.")
def amp(prompt: str) -> str:
    """Run ``amp --dangerously-allow-all -x <prompt>`` with the prompt as one argv element."""
    if not os.environ.get("AMP_API_KEY", "").strip():
        raise RuntimeError("AMP_API_KEY is required to run amp")

    import subprocess

    argv = ["amp", "--dangerously-allow-all", "-x", prompt]
    result = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=600,
        shell=False,
        cwd="/app" if os.path.isdir("/app") else None,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(detail or f"amp exited {result.returncode}")
    return result.stdout


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
