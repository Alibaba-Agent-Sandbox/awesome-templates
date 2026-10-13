"""openclaw — OpenClaw AI Agent 网关沙箱命令。"""
from __future__ import annotations

from agent_sandbox.server import command, start


@command("gateway", description="Start or manage the OpenClaw gateway server.")
def gateway(action: str = "start") -> str:
    """Start or manage the OpenClaw gateway server."""
    import subprocess

    result = subprocess.run(
        ["openclaw", action],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return result.stdout


if __name__ == "__main__":
    import os

    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
