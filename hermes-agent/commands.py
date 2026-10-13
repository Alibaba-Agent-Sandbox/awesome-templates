"""hermes-agent — NousResearch Hermes Agent 沙箱命令。"""
from __future__ import annotations

from agent_sandbox.server import command, start


@command("hermes", description="Run Hermes agent with a prompt.")
def hermes(prompt: str, model: str = "hermes-3-llama-3.1-8b") -> str:
    """Run Hermes agent with a prompt."""
    import subprocess

    result = subprocess.run(
        ["python", "-c", (
            "import json, openai; "
            f"c = openai.OpenAI(); "
            f"r = c.chat.completions.create("
            f"model={model!r}, "
            f"messages=[{{'role':'user','content':{prompt!r}}}]); "
            f"print(json.dumps({{'content': r.choices[0].message.content}}))"
        )],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return result.stdout



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



@command("run", description="Run a Hermes agent script.")
def run(script: str = "main.py") -> str:
    """Run a Python script (``python3 {script}``)."""
    return _run(["python3", script], timeout=120)


if __name__ == "__main__":
    import os

    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
