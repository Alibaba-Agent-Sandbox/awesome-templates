"""Named commands for the template scaffold.

``agent-sandbox-server serve --commands`` imports this module. ``start()``
runs only under ``python3 commands.py`` (the local e2e).
"""
from __future__ import annotations

import os

from agent_sandbox.server import command, start


@command("hello", description="Say hello.")
def hello(name: str = "World") -> str:
    """Return a greeting. ``name`` is a string and defaults to World."""
    return f"Hello, {name}!"


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
