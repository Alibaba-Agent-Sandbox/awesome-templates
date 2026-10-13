"""python-hello — teaching template for the in-sandbox server.

Shows ``@command`` named commands, a hidden command, a custom HTTP route and the
``start()`` entry point. The server freezes the registry when it starts.
"""
from __future__ import annotations

from agent_sandbox.server import CapabilityGroup, ServerResponse, command, default_table, start

table = default_table()


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


@command("hello", description="Say hello.")
def hello(name: str = "World") -> str:
    """Say hello."""
    return f"Hello, {name}!"


@command("run_script", description="Execute Python code and return stdout.")
def run_script(code: str) -> str:
    """Execute Python code and return stdout."""
    import subprocess

    result = subprocess.run(
        ["python3", "-c", code], capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return result.stdout


@command("run", description="Run a Python script.")
def run(file: str = "main.py") -> str:
    """Run a Python script (``python3 {file}``)."""
    return _run(["python3", file], timeout=60)


@command("test", description="Run tests with pytest.")
def test(path: str = ".") -> str:
    """Run pytest (``python3 -m pytest {path}``)."""
    return _run(["python3", "-m", "pytest", path], timeout=120)


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
    import os

    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
