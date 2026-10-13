#!/usr/bin/env python3
"""Run every template e2e against a locally started ``commands.py``.

For each template directory this script:

1. binds an ephemeral port,
2. starts ``python3 commands.py`` in that directory,
3. sets ``E2E_BASE_URL`` to the local server,
4. runs ``e2e_test.py``,
5. stops the server.

No cloud credentials are passed to the server or the test. Every template
must start and its ``e2e_test.py`` must exit 0. A case inside a template
may still record SKIP (no model key, no Playwright); that does not fail
the template.
"""
from __future__ import annotations

import ast
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEALTH_TIMEOUT = 20.0

# Names that would let a test call a hosted model. The local suite never forwards them.
_SECRET_NAMES = {
    "ANTHROPIC_API_KEY",
    "DASHSCOPE_API_KEY",
    "DEEPSEEK_API_KEY",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
}


def _templates() -> list[Path]:
    found: list[Path] = []
    for child in sorted(ROOT.iterdir()):
        if not child.is_dir():
            continue
        if (child / "commands.py").is_file() and (child / "e2e_test.py").is_file():
            found.append(child)
    return found


def _top_level_modules(source: str) -> list[str]:
    tree = ast.parse(source)
    modules: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            modules.extend(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.append(node.module.split(".", 1)[0])
    return modules


def _missing_imports(source: str) -> list[str]:
    missing: list[str] = []
    for name in _top_level_modules(source):
        if name == "agent_sandbox" or name in sys.stdlib_module_names:
            continue
        try:
            __import__(name)
        except Exception as exc:  # noqa: BLE001
            missing.append(f"{name} ({type(exc).__name__}: {exc})")
    return missing


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _child_env(base_dir: str, port: int, pty_port: int, path_prefix: str) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key not in _SECRET_NAMES}
    for key in list(env):
        if key.endswith("_API_KEY") or key.endswith("_SECRET") or key.endswith("_TOKEN"):
            env.pop(key, None)
    env["PATH"] = path_prefix + os.pathsep + env.get("PATH", "")
    env["ABX_SERVER_PORT"] = str(port)
    env["ABX_PTY_PORT"] = str(pty_port)
    env["ABX_SERVER_BASE_DIR"] = base_dir
    env["WORKSPACE"] = base_dir
    env["E2E_BASE_URL"] = f"http://127.0.0.1:{port}"
    env["E2E_BASE_DIR"] = base_dir
    env["E2E_WORKSPACE"] = base_dir
    env["E2E_RUN_LLM"] = "0"
    return env


def _python_shim() -> str:
    """Directory prepended to PATH so ``python`` resolves when only ``python3`` exists."""
    if shutil.which("python"):
        return ""
    python3 = shutil.which("python3")
    if not python3:
        return ""
    directory = tempfile.mkdtemp(prefix="e2e-python-shim-")
    os.symlink(python3, os.path.join(directory, "python"))
    return directory


def _drain(stream, bucket: list[str]) -> None:
    try:
        for line in stream:
            bucket.append(line)
    except Exception:
        pass


def _wait_healthy(port: int, proc: subprocess.Popen[str], timeout: float) -> bool:
    url = f"http://127.0.0.1:{port}/health"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                body = json.loads(resp.read().decode())
            if resp.status == 200 and body.get("status") == "ok":
                return True
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            time.sleep(0.2)
    return False


def _stop(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def _startup_skip_reason(text: str) -> str | None:
    """Classify a crash that is a missing binary, module, or API key."""
    lowered = text.lower()
    if "no module named 'agent_sandbox'" in lowered or 'no module named "agent_sandbox"' in lowered:
        return None
    if "modulenotfounderror" in lowered or "importerror" in lowered:
        return "commands.py cannot start because a third-party Python module is missing"
    if any(token in lowered for token in ("api key", "api_key", "apikey")):
        return "commands.py cannot start because an API key is required"
    if any(token in lowered for token in ("filenotfounderror", "command not found", "no such file or directory")):
        return "commands.py cannot start because a third-party binary is missing"
    return None


def _cleanup(directory: Path) -> None:
    pycache = directory / "__pycache__"
    if pycache.is_dir():
        shutil.rmtree(pycache, ignore_errors=True)
    for child in directory.iterdir():
        name = child.name
        if name.startswith("abx_e2e_") and child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
        elif name != "e2e_test.py" and (
            name.startswith("e2e_") or name.startswith(".e2e_") or name.startswith("screenshot_")
        ):
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)


def _run_one(directory: Path, path_prefix: str) -> tuple[str, str]:
    """Return ``(status, detail)`` for one template. status is pass or fail."""
    name = directory.name
    source = (directory / "commands.py").read_text(encoding="utf-8")

    missing = _missing_imports(source)
    if missing:
        reason = "commands.py cannot start without third-party module(s): " + "; ".join(missing)
        return "fail", reason

    port = _free_port()
    pty_port = _free_port()
    env = _child_env(str(directory), port, pty_port, path_prefix)
    stdout: list[str] = []
    stderr: list[str] = []
    proc = subprocess.Popen(
        ["python3", "commands.py"],
        cwd=directory,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    threading.Thread(target=_drain, args=(proc.stdout, stdout), daemon=True).start()
    threading.Thread(target=_drain, args=(proc.stderr, stderr), daemon=True).start()

    try:
        healthy = _wait_healthy(port, proc, HEALTH_TIMEOUT)
        log = "".join(stderr)[-2000:]
        if not healthy:
            detail = log.strip() or f"process exited {proc.poll()} before /health"
            reason = _startup_skip_reason(detail)
            if reason:
                return "fail", f"{name} must start with the server SDK, but {reason}: {detail[:400]}"
            return "fail", f"server did not become healthy: {detail[:400]}"

        test = subprocess.run(
            ["python3", "e2e_test.py"],
            cwd=directory,
            env=env,
            check=False,
        )
        if test.returncode != 0:
            return "fail", f"e2e_test.py exited {test.returncode}"
        return "pass", f"http://127.0.0.1:{port}"
    finally:
        _stop(proc)
        _cleanup(directory)


def main() -> int:
    templates = _templates()
    if not templates:
        print("no template directories found", flush=True)
        return 1

    shim = _python_shim()
    results: list[tuple[str, str, str]] = []
    try:
        for directory in templates:
            print("\n" + "=" * 74, flush=True)
            print(f"TEMPLATE {directory.name}", flush=True)
            print("=" * 74, flush=True)
            status, detail = _run_one(directory, shim)
            results.append((directory.name, status, detail))
            print(f"[{status.upper()}] {directory.name} — {detail}", flush=True)
    finally:
        if shim:
            shutil.rmtree(shim, ignore_errors=True)

    passed = [name for name, status, _ in results if status == "pass"]
    failed = [(name, detail) for name, status, detail in results if status != "pass"]

    print("\n" + "=" * 74, flush=True)
    print("LOCAL E2E SUMMARY", flush=True)
    print("=" * 74, flush=True)
    print(
        f"{len(passed)} passed, {len(failed)} failed (total {len(results)})",
        flush=True,
    )
    for name, detail in failed:
        print(f"  fail {name}: {detail}", flush=True)
    print("=" * 74, flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
