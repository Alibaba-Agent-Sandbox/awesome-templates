"""node-web — Node.js Web 服务沙箱命令。"""
from __future__ import annotations

from easy_sandbox.server import (
    CapabilityGroup,
    CommandRegistry,
    SandboxServer,
    default_table,
)

# ---------------------------------------------------------------------------
# Route table — enable capability groups
# ---------------------------------------------------------------------------

table = default_table()
table.enable_group(CapabilityGroup.FILE_OPS)   # upload/download + file operations
table.enable_group(CapabilityGroup.PROCESS)    # shell + process management
table.enable_group(CapabilityGroup.SYSTEM)     # system info + port detection (Web service)

# ---------------------------------------------------------------------------
# Command registry
# ---------------------------------------------------------------------------

registry = CommandRegistry()


@registry.command("serve", description="Start Node.js app.")
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


registry.freeze()

if __name__ == "__main__":
    import os

    _port = int(os.environ.get("EBX_SERVER_PORT", "9000"))
    server = SandboxServer(registry=registry)
    server.serve(port=_port)
