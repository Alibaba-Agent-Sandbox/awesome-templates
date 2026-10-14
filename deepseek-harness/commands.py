"""deepseek-harness — DeepSeek Agent Runtime 沙箱命令。"""
from __future__ import annotations

from agent_sandbox.server import command, start


@command("deepseek", description="Run DeepSeek agent with a prompt.")
def deepseek(prompt: str, model: str = "deepseek-coder") -> str:
    """Call the DeepSeek API. The prompt is passed in the environment, not interpolated."""
    import os
    import subprocess

    key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY is not set")
    script = (
        "import json, os\n"
        "from openai import OpenAI\n"
        "client = OpenAI(api_key=os.environ['DEEPSEEK_API_KEY'], "
        "base_url=os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com'))\n"
        "reply = client.chat.completions.create("
        "model=os.environ.get('DEEPSEEK_MODEL', 'deepseek-coder'), "
        "messages=[{'role': 'user', 'content': os.environ['DEEPSEEK_PROMPT']}])\n"
        "print(json.dumps({'content': reply.choices[0].message.content}))\n"
    )
    env = os.environ.copy()
    env["DEEPSEEK_API_KEY"] = key
    env["DEEPSEEK_PROMPT"] = prompt
    env["DEEPSEEK_MODEL"] = model
    result = subprocess.run(
        ["python3", "-c", script],
        capture_output=True, text=True, timeout=120, env=env,
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



@command("run", description="Run a Python script in the DeepSeek agent environment.")
def run(script: str = "main.py") -> str:
    """Run a Python script (``python3 {script}``)."""
    return _run(["python3", script], timeout=120)


if __name__ == "__main__":
    import os

    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
