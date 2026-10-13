"""qwen-code — 通义千问编码 Agent 沙箱命令。"""
from __future__ import annotations

from agent_sandbox.server import command, start


@command("qwen", description="Run Qwen Code agent for natural-language deployment.")
def qwen(prompt: str, max_turns: int = 100) -> str:
    """Run qwen-code (``qwen -p`` with ``--yolo`` and JSON output)."""
    return _run(
        [
            "qwen", "-p", prompt,
            "--yolo",
            "--output-format", "json",
            "--max-turns", str(max_turns),
        ],
        timeout=600,
    )



def _run(argv: list[str], *, timeout: int, cwd: str = "/app") -> str:
    """Run *argv* in ``/app`` when that directory exists and return stdout."""
    import os
    import subprocess

    workdir = cwd if os.path.isdir(cwd) else (os.environ.get("WORKSPACE") or os.getcwd())
    result = subprocess.run(
        argv, cwd=workdir, capture_output=True, text=True, timeout=timeout,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(detail or f"command exited {result.returncode}")
    return result.stdout



@command("run", description="Run a Python script in the Qwen Code environment.")
def run(script: str = "main.py") -> str:
    """Run a Python script (``python3 {script}``)."""
    return _run(["python3", script], timeout=120)


if __name__ == "__main__":
    import os

    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
