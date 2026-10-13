"""qoder — Qoder AI 编程助手沙箱命令。"""
from __future__ import annotations

from agent_sandbox.server import command, start


@command("qoder_run", description="Run a Python script in the Qoder environment.")
def qoder_run(script: str = "main.py") -> str:
    """Run a Python script (``python3 {script}``)."""
    return _run(["python3", script], timeout=120)



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


if __name__ == "__main__":
    import os

    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
