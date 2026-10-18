"""python-hello — teaching template for the in-sandbox server.

Shows ``@command`` named commands, a hidden command, a custom HTTP route and the
``start()`` entry point. The server freezes the registry when it starts.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

from agent_sandbox.server import CapabilityGroup, ServerResponse, command, default_table, start

table = default_table()


def _run(argv: list[str], *, timeout: float) -> str:
    """Use WORKSPACE, or this module's directory, for every Python command."""
    workdir = os.environ.get("WORKSPACE") or str(Path(__file__).resolve().parent)
    try:
        result = subprocess.run(
            argv, cwd=workdir, capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        # TimeoutExpired includes argv, including the full inline source code.
        raise RuntimeError("Python command exceeded its execution deadline; output omitted") from None
    except OSError:
        # OS errors can include user-provided file paths or other request data.
        raise RuntimeError("Python command could not start; request details omitted") from None
    if result.returncode != 0:
        raise RuntimeError(f"Python command exited {result.returncode}; output omitted")
    return result.stdout


@command("hello", description="Say hello.")
def hello(name: str = "World") -> str:
    """Say hello."""
    return f"Hello, {name}!"


@command("run_script", description="Execute Python code and return stdout.")
def run_script(code: str) -> str:
    """Execute Python code and return stdout."""
    return _run([sys.executable, "-c", code], timeout=30)


@command("run", description="Run a Python script.")
def run(file: str = "main.py") -> str:
    """Run a Python script (``python3 {file}``)."""
    return _run([sys.executable, file], timeout=60)


@command("test", description="Run tests with pytest.")
def test(path: str = ".") -> str:
    """Run pytest (``python3 -m pytest {path}``)."""
    return _run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", path], timeout=120)


@command(hidden=True)
def _debug_info() -> dict:
    """Internal debug command — not listed in /commands."""
    import platform

    return {"python": platform.python_version(), "system": platform.system()}


# ---------------------------------------------------------------------------
# Custom HTTP route via RouteTable.route() decorator
# ---------------------------------------------------------------------------


@table.route("GET", "/hello/{name}", group=CapabilityGroup.COMMANDS)
def hello_route(request: object) -> ServerResponse:
    """Custom route: GET /hello/{name} returns a greeting as JSON."""
    name = getattr(request, "path_params", {}).get("name", "World")
    return ServerResponse.ok({"greeting": f"Hello, {name}!"})


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
