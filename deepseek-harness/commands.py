"""A bounded DeepSeek Chat Completions tool loop for sandbox coding tasks."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import time
import threading

import httpx
from agent_sandbox.server import command, start


def _redact(text: str) -> str:
    for name, value in sorted(os.environ.items(), key=lambda item: len(item[1]), reverse=True):
        if value and any(word in name.upper() for word in ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")):
            for variant in (json.dumps(value)[1:-1], json.dumps(value, ensure_ascii=False)[1:-1], value):
                text = text.replace(variant, "[REDACTED]")
    return text


def _workdir(cwd: str = "") -> Path:
    root = Path(os.environ.get("WORKSPACE") or "/home/user/app")
    path = Path(cwd) if cwd else root
    if not path.is_absolute():
        path = root / path
    if not path.is_dir():
        raise ValueError("cwd must name an existing directory")
    return path.resolve()


def _path(root: Path, name: str) -> Path:
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        raise ValueError("file path must remain inside cwd")
    return path


# Generated from scripts/process_runners/text.py; update with scripts/sync_process_runners.py.
def _run_process(argv: list[str], *, cwd: str, timeout: int | float,
                 env: dict | None = None, input_text: str | None = None) -> tuple[int, str, str]:
    """Keep the Linux session leader unreaped until its owned group is stopped."""
    process = subprocess.Popen(argv, cwd=cwd, env=env,
        stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    stdout_parts: list[bytes] = []
    stderr_parts: list[bytes] = []
    def drain(stream, parts):
        try:
            while chunk := stream.read(65536):
                parts.append(chunk)
        except OSError:
            pass
        finally:
            stream.close()
    readers = [threading.Thread(target=drain, args=(process.stdout, stdout_parts), daemon=True),
               threading.Thread(target=drain, args=(process.stderr, stderr_parts), daemon=True)]
    for reader in readers:
        reader.start()
    if input_text is not None:
        def feed():
            try:
                process.stdin.write(input_text.encode())
                process.stdin.close()
            except (OSError, ValueError):
                pass
            finally:
                try:
                    process.stdin.close()
                except (OSError, ValueError):
                    pass
        threading.Thread(target=feed, daemon=True).start()
    deadline = time.monotonic() + timeout
    timed_out = False
    try:
        while os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is None:
            if time.monotonic() >= deadline:
                timed_out = True
                break
            time.sleep(0.02)
    finally:
        # WNOWAIT pins the original PID/PGID even after leader exit. No poll(),
        # wait() or communicate() may reap it before group cleanup.
        if timed_out:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            grace = time.monotonic() + 1
            while time.monotonic() < grace:
                if os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None:
                    break
                time.sleep(0.02)
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            raise RuntimeError("owned process cleanup timed out") from None
        for reader in readers:
            reader.join(timeout=2)
    if timed_out:
        raise RuntimeError(f"command timed out after {timeout} seconds") from None
    return (process.returncode, b"".join(stdout_parts).decode("utf-8", "replace"),
            b"".join(stderr_parts).decode("utf-8", "replace"))


def _shell(command: str, cwd: Path, timeout: float) -> str:
    env = {name: value for name, value in os.environ.items() if not any(
        part in name.upper() for part in ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL"))}
    code, stdout, stderr = _run_process(["/bin/sh", "-c", command], cwd=str(cwd), timeout=timeout, env=env)
    return json.dumps({"exit_code": code, "stdout": _redact(stdout[-65536:]),
                       "stderr": _redact(stderr[-65536:])})


_PARAMS = {
    "read_file": ({"path": {"type": "string"}}, ["path"]),
    "write_file": ({"path": {"type": "string"}, "content": {"type": "string"}}, ["path", "content"]),
    "list_files": ({"path": {"type": "string"}}, ["path"]),
    "run_shell": ({"command": {"type": "string"}}, ["command"]),
}
TOOLS = [{"type": "function", "function": {"name": name,
          "description": {"read_file": "Read a UTF-8 file relative to cwd (up to 128 KiB).",
                          "write_file": "Write a UTF-8 file relative to cwd, creating parent directories.",
                          "list_files": "List a directory relative to cwd.",
                          "run_shell": "Run a shell command in cwd; may modify sandbox files. No model credentials are inherited."}[name],
          "parameters": {"type": "object", "properties": props, "required": required,
                         "additionalProperties": False}}} for name, (props, required) in _PARAMS.items()]


def _tool(name: str, args: dict, root: Path, remaining: float) -> str:
    if name not in _PARAMS or not isinstance(args, dict):
        raise ValueError("unknown tool or invalid arguments")
    props, required = _PARAMS[name]
    if set(args) != set(required) or any(not isinstance(args[k], str) for k in required):
        raise ValueError("tool arguments must match the declared string fields")
    if name == "run_shell":
        return _shell(args["command"], root, min(60, remaining))
    path = _path(root, args["path"])
    if name == "read_file":
        with path.open("rb") as source:
            return source.read(131072).decode("utf-8", "replace")
    if name == "write_file":
        if len(args["content"].encode()) > 131072:
            raise ValueError("write exceeds 128 KiB")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(args["content"], encoding="utf-8")
        return "written"
    return json.dumps(sorted(p.name for p in path.iterdir())[:1000])


@command("deepseek_tools", description="List registered coding tools without a model request.")
def deepseek_tools() -> str:
    return ",".join(sorted(_PARAMS))


@command("deepseek_setup_check", description="Inspect model/key availability without contacting the API.")
def deepseek_setup_check() -> dict:
    return {"api_key_set": bool((os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY") or "").strip()),
            "model": os.environ.get("DEEPSEEK_MODEL") or "deepseek-flash",
            "workspace": str(_workdir()), "tools": sorted(_PARAMS)}


@command("deepseek", description="Run a bounded DeepSeek tool loop that can read, edit and test sandbox files.")
def deepseek(prompt: str, model: str = "", cwd: str = "", max_turns: int = 20,
             command_timeout: int = 600) -> str:
    if not prompt.strip():
        raise ValueError("prompt must not be empty")
    if not 1 <= max_turns <= 100 or not 1 <= command_timeout <= 1800:
        raise ValueError("max_turns must be 1..100 and command_timeout must be 1..1800 seconds")
    root = _workdir(cwd)
    if not (os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY") or "").strip():
        raise RuntimeError("DEEPSEEK_API_KEY or OPENAI_API_KEY is required")
    code, stdout, stderr = _run_process([sys.executable, str(Path(__file__).resolve()), "--agent-worker"],
        cwd=str(root), env=os.environ.copy(), timeout=command_timeout,
        input_text=json.dumps({"prompt": prompt, "model": model, "cwd": str(root),
                               "max_turns": max_turns, "command_timeout": command_timeout}))
    if code:
        raise RuntimeError(_redact(stderr).strip() or "DeepSeek worker failed")
    return _redact(stdout).rstrip("\n")


def _agent_loop(prompt: str, model: str = "", cwd: str = "", max_turns: int = 20,
             command_timeout: int = 600) -> str:
    if not prompt.strip():
        raise ValueError("prompt must not be empty")
    if not 1 <= max_turns <= 100 or not 1 <= command_timeout <= 1800:
        raise ValueError("max_turns must be 1..100 and command_timeout must be 1..1800 seconds")
    root = _workdir(cwd)
    key = (os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY or OPENAI_API_KEY is required")
    endpoint = (os.environ.get("DEEPSEEK_BASE_URL") or "https://api.deepseek.com").rstrip("/")
    selected_model = model or os.environ.get("DEEPSEEK_MODEL") or "deepseek-flash"
    messages = [{"role": "system", "content": "You are a coding agent. Use tools to inspect, edit, and test files in cwd. Complete the requested file changes before answering."},
                {"role": "user", "content": prompt}]
    deadline = time.monotonic() + command_timeout
    tool_calls = 0
    with httpx.Client(headers={"Authorization": "Bearer " + key}, follow_redirects=False) as client:
        for _ in range(max_turns):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError("DeepSeek command timed out")
            try:
                response = client.post(endpoint + "/chat/completions", json={"model": selected_model,
                    "messages": messages, "tools": TOOLS}, timeout=min(remaining, 120))
                response.raise_for_status()
                message = response.json()["choices"][0]["message"]
            except Exception as exc:
                raise RuntimeError(f"DeepSeek request failed ({type(exc).__name__}); details omitted") from None
            calls = message.get("tool_calls") or []
            if not calls:
                return _redact(json.dumps({"content": message.get("content") or "", "tool_calls": tool_calls}))
            messages.append(message)
            for call in calls:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RuntimeError("DeepSeek command timed out")
                try:
                    result = _tool(call["function"]["name"], json.loads(call["function"]["arguments"]), root, remaining)
                except Exception as exc:
                    result = "Tool failed: " + type(exc).__name__
                tool_calls += 1
                messages.append({"role": "tool", "tool_call_id": call["id"], "content": _redact(result)})
    raise RuntimeError("DeepSeek tool loop reached max_turns without a final response")


@command("run", description="Run a local Python script (compatibility command).")
def run(script: str = "main.py") -> str:
    result = json.loads(_shell("exec " + shlex.quote(sys.executable) + " " + shlex.quote(script), _workdir(), 120))
    if result["exit_code"]:
        raise RuntimeError(result["stderr"] or result["stdout"] or "script failed")
    return result["stdout"]


if __name__ == "__main__":
    if sys.argv[1:] == ["--agent-worker"]:
        class WorkerCancelled(BaseException):
            pass
        def cancel_worker(signum, frame):
            # Unwind an active shell runner's finally before the outer owner
            # uses SIGKILL. Shell tools have separate owned process groups.
            raise WorkerCancelled()
        signal.signal(signal.SIGTERM, cancel_worker)
        try:
            print(_agent_loop(**json.load(sys.stdin)))
        except WorkerCancelled:
            print("DeepSeek command cancelled", file=sys.stderr)
            sys.exit(1)
        except Exception as exc:
            # Avoid traceback source/arguments, provider bodies and private prompts.
            print(_redact(str(exc)) if isinstance(exc, RuntimeError) else "DeepSeek worker failed", file=sys.stderr)
            sys.exit(1)
    else:
        start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
