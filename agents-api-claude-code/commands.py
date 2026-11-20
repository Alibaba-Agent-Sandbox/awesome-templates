"""Local version diagnostics; the managed guest does not expose command routes."""
from __future__ import annotations

import os
import json
from pathlib import Path
import shutil
import subprocess

from agent_sandbox.server import command, start


@command("agents_version", description="Check pinned CLI versions locally without calling a model.")
def agents_version() -> str:
    profile_path = Path(__file__).with_name("harness.json")
    if not profile_path.is_file():
        profile_path = Path(__file__).with_name("server") / "harness.json"
    profile = json.loads(profile_path.read_text())
    executable = shutil.which(profile["binary"])
    if executable is None:
        raise RuntimeError("The pinned Agent CLI is unavailable")
    result = subprocess.run([executable, "--version"], capture_output=True, text=True, timeout=20, check=False)
    if result.returncode or profile["version"] not in result.stdout.strip().split():
        raise RuntimeError("The Agent CLI does not match its template version")
    return profile["adapter"] + " " + profile["version"]


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
