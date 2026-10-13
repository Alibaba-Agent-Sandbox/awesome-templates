"""node-web — Node.js Web 服务沙箱命令。"""
from __future__ import annotations

from agent_sandbox.server import command
from agent_sandbox.server import start as serve_http


@command("serve", description="Start Node.js app.")
def serve(entry: str = "index.js", port: int = 3000) -> dict:
    """Start a Node.js web application server."""
    import os
    import subprocess
    import time

    env = {**os.environ, "PORT": str(port)}
    proc = subprocess.Popen(
        ["node", entry],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    # 等待短暂时间确认进程启动
    time.sleep(1)
    if proc.poll() is not None:
        # 进程已退出，说明启动失败
        stdout, stderr = proc.communicate()
        raise RuntimeError(f"Server failed to start: {stderr or stdout}")
    return {
        "pid": proc.pid,
        "port": port,
        "entry": entry,
        "status": "running",
    }



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



@command("dev", description="Start development server with hot reload.")
def dev() -> str:
    """Run ``npm run dev``."""
    return _run(["npm", "run", "dev"], timeout=120)


@command("build", description="Build production bundle.")
def build() -> str:
    """Run ``npm run build``."""
    return _run(["npm", "run", "build"], timeout=120)


@command("start", description="Start production server.")
def start() -> str:
    """Run ``npm start``."""
    return _run(["npm", "start"], timeout=120)


if __name__ == "__main__":
    import os

    serve_http(int(os.environ.get("ABX_SERVER_PORT", "9000")))
