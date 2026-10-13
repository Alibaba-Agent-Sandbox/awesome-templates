"""codex — OpenAI Codex CLI Agent 沙箱命令。"""
from __future__ import annotations

from agent_sandbox.server import command, start


@command("codex", description="Run Codex agent.")
def codex(prompt: str, model: str = "codex-mini") -> str:
    """Run Codex agent."""
    import subprocess

    result = subprocess.run(
        [
            "codex", "-p", prompt,
            "--model", model,
            "--yolo",
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
