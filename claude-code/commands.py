"""claude-code — Anthropic Claude Code Agent 沙箱命令。"""
from __future__ import annotations

from agent_sandbox.server import command, start


@command("claude", description="Run Claude Code agent.")
def claude(prompt: str, model: str = "sonnet") -> str:
    """Run Claude Code agent."""
    import subprocess

    result = subprocess.run(
        [
            "claude", "-p", prompt,
            "--model", model,
            "--output-format", "json",
        ],
        capture_output=True, text=True, timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return result.stdout


if __name__ == "__main__":
    import os

    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
