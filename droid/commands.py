"""droid — Factory Droid 编码 CLI 沙箱命令。"""
from __future__ import annotations

from agent_sandbox.server import command, start


@command("droid", description="Run Factory Droid headless (droid exec).")
def droid(prompt: str) -> str:
    """Run ``droid exec`` with *prompt* as its own argv element."""
    import os
    import subprocess

    if not os.environ.get("FACTORY_API_KEY", "").strip():
        raise RuntimeError("FACTORY_API_KEY is required")

    workdir = "/app"
    if not os.path.isdir(workdir):
        workdir = os.environ.get("WORKSPACE") or os.getcwd()

    argv = ["droid", "exec", prompt]
    result = subprocess.run(
        argv,
        cwd=workdir,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(detail or f"droid exec exited {result.returncode}")
    return result.stdout


if __name__ == "__main__":
    import os

    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
