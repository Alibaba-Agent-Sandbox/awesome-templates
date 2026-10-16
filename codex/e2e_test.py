#!/usr/bin/env python3
"""HTTP smoke and optional real coding acceptance against E2E_BASE_URL.

Express runs go through scripts/express_e2e.py. This file does not create a
cloud sandbox. A model call is SKIP unless E2E_RUN_LLM=1 and a key is visible
in this process (the server process needs the same key).
"""
from __future__ import annotations

import base64
import os
import shlex
import sys
import uuid

import httpx

BASE_URL = os.environ.get("E2E_BASE_URL", "http://127.0.0.1:9000").rstrip("/")
WORK = os.environ.get("E2E_WORKSPACE") or os.environ.get("E2E_BASE_DIR") or "/home/user/workspace"
TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=10.0)
LLM_TIMEOUT = float(os.environ.get("E2E_LLM_TIMEOUT", "420"))
RUN_LLM = os.environ.get("E2E_RUN_LLM", "").strip().lower()
REQUIRE = os.environ.get("E2E_REQUIRE_LLM", "").strip().lower() in {"1", "true", "yes"}
MODEL = os.environ.get("E2E_MODEL", "").strip()
MARKER = "ABX_E2E_OK"
TOKEN = os.environ.get("E2E_TOKEN", "")
PROBE_ROOT = os.path.join(WORK, "abx_e2e_codex_" + uuid.uuid4().hex)
KEY_ENVS = ("OPENAI_API_KEY", "CODEX_API_KEY", "ABX_LLM_API_KEY")
COMMANDS = {
    "codex_version",
    "codex_setup_check",
    "codex_exec",
    "codex_config_write",
    "codex_agents_write",
    "codex",
}


def _read_file(client: httpx.Client, path: str) -> str:
    response = client.get("/files/download-stream", params={"path": path})
    response.raise_for_status()
    return base64.b64decode(response.json()["content_base64"]).decode("utf-8")


def _exists(client: httpx.Client, path: str) -> bool:
    response = client.get("/files/stat", params={"path": path})
    response.raise_for_status()
    return response.json().get("exists") is True


def main() -> int:
    headers = {"X-Access-Token": TOKEN} if TOKEN else {}
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT, headers=headers) as client:
        status = 1
        try:
            status = _run_checks(client)
        finally:
            try:
                response = client.delete("/files", params={"path": PROBE_ROOT})
                if response.status_code not in {200, 404}:
                    print(f"[FAIL] owned probe cleanup HTTP {response.status_code}", flush=True)
                    status = 1
            except httpx.HTTPError:
                print("[FAIL] owned probe cleanup transport error", flush=True)
                status = 1
        return status


def _run_checks(client: httpx.Client) -> int:
    failures = 0
    home = os.path.join(PROBE_ROOT, "home")
    workspace = os.path.join(PROBE_ROOT, "workspace")

    def check(label: str, ok: bool, detail: str = "") -> None:
        nonlocal failures
        print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""), flush=True)
        failures += not ok

    health = client.get("/health")
    check("GET /health", health.status_code == 200 and health.json().get("status") == "ok")

    listed = client.get("/commands")
    body = listed.json()
    entries = {item.get("name"): item for item in body.get("commands", []) if isinstance(item, dict)}
    check("GET /commands", listed.status_code == 200 and COMMANDS <= set(entries), str(sorted(entries)))

    exec_args = {item.get("name"): item.get("type") for item in entries.get("codex_exec", {}).get("args", [])}
    check(
        "codex_exec arg types",
        exec_args.get("prompt") == "string"
        and exec_args.get("json_events") == "boolean"
        and exec_args.get("timeout_s") == "integer"
        and exec_args.get("resume_all") == "boolean"
        and exec_args.get("sandbox") == "string",
        str(sorted(exec_args)),
    )

    unknown = client.post("/commands/__no_such_command__", json={})
    check("unknown command", unknown.status_code == 404 and unknown.json().get("type") == "ValueError")

    missing = client.post("/commands/codex_exec", json={})
    check(
        "codex_exec missing prompt",
        missing.status_code == 400 and "Required argument" in str(missing.json().get("error", "")),
        str(missing.status_code),
    )

    bad_sandbox = client.post(
        "/commands/codex_exec",
        json={"prompt": "do not run", "sandbox": "nope", "cwd": workspace},
    )
    bad_body = bad_sandbox.json()
    check(
        "codex_exec rejects sandbox",
        bad_sandbox.status_code == 500 and bad_body.get("type") == "ValueError",
        str(bad_body.get("error", ""))[:160],
    )

    setup = client.post("/commands/codex_setup_check", json={})
    setup_body = setup.json()
    result = setup_body.get("result") if isinstance(setup_body.get("result"), dict) else {}
    check(
        "codex_setup_check",
        setup.status_code == 200
        and result.get("bypass_flag") == "--dangerously-bypass-approvals-and-sandbox"
        and result.get("full_auto_supported") is False
        and isinstance(result.get("linux_sandbox"), bool)
        and isinstance(result.get("use_bypass"), bool)
        and result.get("pinned_version") == "0.162.1",
        f"linux_sandbox={result.get('linux_sandbox')} binary={result.get('binary_present')}",
    )
    if result.get("binary_present"):
        check(
            "bypass follows the probe",
            result.get("use_bypass") is (not result.get("linux_sandbox")),
        )
        version = client.post("/commands/codex_version", json={})
        version_body = version.json()
        check(
            "codex_version",
            version.status_code == 200 and version_body.get("result") == result.get("version"),
            str(version_body.get("result")),
        )
        if not result.get("linux_sandbox"):
            denied_cwd = os.path.join(workspace, "denied-read-only")
            denied = client.post(
                "/commands/codex_exec",
                json={"prompt": "do not run", "sandbox": "read-only", "cwd": denied_cwd},
            )
            check(
                "read-only is refused without a Linux sandbox",
                denied.status_code == 500
                and denied.json().get("type") == "RuntimeError"
                and "cannot honor sandbox='read-only'" in denied.json().get("error", "")
                and not _exists(client, denied_cwd),
            )
    else:
        version = client.post("/commands/codex_version", json={})
        check(
            "codex_version without binary",
            version.status_code == 500 and "not on PATH" in str(version.json().get("error", "")),
        )

    config = client.post(
        "/commands/codex_config_write",
        json={
            "base_url": "https://example.invalid/v1",
            "provider": "compatible",
            "env_key": "ABX_LLM_API_KEY",
            "model": "qwen-plus",
            "codex_home": home,
        },
    )
    config_body = config.json().get("result") if config.status_code == 200 else {}
    toml = config_body.get("toml", "") if isinstance(config_body, dict) else ""
    check(
        "codex_config_write",
        config.status_code == 200
        and config_body.get("wire_api") == "responses"
        and config_body.get("supports_websockets") is False
        and 'wire_api = "responses"' in toml
        and "supports_websockets = false" in toml
        and "ABX_LLM_API_KEY" in toml
        and "sk-" not in toml
        and _read_file(client, os.path.join(home, "config.toml")) == toml,
        str(config.status_code),
    )

    chat = client.post(
        "/commands/codex_config_write",
        json={"base_url": "https://example.invalid/v1", "wire_api": "chat", "codex_home": home},
    )
    check(
        "wire_api chat rejected",
        chat.status_code == 500 and chat.json().get("type") == "ValueError",
        str(chat.json().get("error", ""))[:160],
    )

    reserved = client.post(
        "/commands/codex_config_write",
        json={"base_url": "https://example.invalid/v1", "provider": "openai", "codex_home": home},
    )
    check(
        "reserved provider rejected",
        reserved.status_code == 500 and reserved.json().get("type") == "ValueError",
    )

    agents = client.post(
        "/commands/codex_agents_write",
        json={"content": "Reply with the marker when asked.\n", "cwd": workspace},
    )
    agents_body = agents.json().get("result") if agents.status_code == 200 else {}
    path = agents_body.get("path", "") if isinstance(agents_body, dict) else ""
    check(
        "codex_agents_write",
        agents.status_code == 200 and path.endswith("/AGENTS.md") and _read_file(client, path) == "Reply with the marker when asked.\n",
        path,
    )

    _llm(client, check)

    return 1 if failures else 0


def _agent_result_ok(result: dict) -> bool:
    """Input echoed in a tool event is not evidence of a completed agent task."""
    completed_command = any(
        isinstance(event, dict)
        and event.get("type") == "item.completed"
        and isinstance(event.get("item"), dict)
        and event["item"].get("type") == "command_execution"
        and event["item"].get("status") == "completed"
        and event["item"].get("exit_code") == 0
        for event in result.get("events", [])
    )
    return result.get("last_message", "").strip() == MARKER and completed_command


def _llm(client: httpx.Client, check) -> None:
    test = "codex_exec real coding task"
    forced_off = RUN_LLM in {"0", "false", "no"}
    enabled = RUN_LLM in {"1", "true", "yes"} or REQUIRE
    has_key = any(os.environ.get(name, "").strip() for name in KEY_ENVS)
    if REQUIRE and forced_off:
        check(test, False, "E2E_REQUIRE_LLM=1 conflicts with E2E_RUN_LLM=0")
        return
    if forced_off or not enabled or not has_key:
        print(f"[SKIP] {test}", flush=True)
        if REQUIRE or RUN_LLM in {"1", "true", "yes"}:
            check(test, False, "model key or E2E_RUN_LLM is missing")
        return
    task = os.path.join(PROBE_ROOT, "agent-task")
    payload: dict = {
        "prompt": (
            "Create fibonacci.py implementing fib(n): fib(0)=0, fib(1)=1, "
            "and negative input raises ValueError. Create test_fibonacci.py using "
            "stdlib unittest to cover zero, positive, and negative inputs. Run the "
            "tests with python3 -m unittest -v test_fibonacci.py using your command "
            "tool. After the tests pass, write acceptance.txt containing exactly "
            f"{MARKER} followed by a newline. Reply with exactly: {MARKER}"
        ),
        "cwd": task,
        "sandbox": "auto",
        "json_events": True,
        "ephemeral": True,
        "timeout_s": max(1, min(3600, int(LLM_TIMEOUT) - 30)),
    }
    if MODEL:
        payload["model"] = MODEL
    response = client.post("/commands/codex_exec", json=payload, timeout=LLM_TIMEOUT)
    body = response.json()
    result = body.get("result") if isinstance(body.get("result"), dict) else {}
    completed = _agent_result_ok(result)
    try:
        files_ok = (
            _read_file(client, os.path.join(task, "acceptance.txt")) == MARKER + "\n"
            and bool(_read_file(client, os.path.join(task, "fibonacci.py")).strip())
            and bool(_read_file(client, os.path.join(task, "test_fibonacci.py")).strip())
        )
    except (httpx.HTTPError, KeyError, ValueError):
        files_ok = False
    check(test, response.status_code == 200 and completed and files_ok,
          f"HTTP {response.status_code} agent_tools={completed} artifacts={files_ok}")
    if response.status_code != 200 or not completed or not files_ok:
        return
    assertions = (
        "from fibonacci import fib\n"
        "assert [fib(n) for n in (0, 1, 2, 7, 10)] == [0, 1, 1, 13, 55]\n"
        "try:\n fib(-1)\nexcept ValueError:\n pass\nelse:\n raise AssertionError('negative input accepted')\n"
    )
    # /shell uses shlex.split + exec, not a shell interpreter. Supply cwd as
    # an API argument and keep operators such as `cd` / `&&` out of argv.
    shell_prefix = "env -i PATH=/usr/local/bin:/usr/bin:/bin python3 "
    verified = client.post("/shell", json={
        "command": shell_prefix + "-c " + shlex.quote(assertions), "cwd": task, "timeout": 30,
    })
    check("independent remote Fibonacci assertions", verified.status_code == 200
          and verified.json().get("exit_code") == 0)
    tests = client.post("/shell", json={
        "command": shell_prefix + "-m unittest -v test_fibonacci.py", "cwd": task, "timeout": 30,
    })
    check("remote agent-written unittest rerun", tests.status_code == 200
          and tests.json().get("exit_code") == 0
          and "Ran 0 tests" not in tests.json().get("stderr", "")
          and "Ran " in tests.json().get("stderr", ""))


if __name__ == "__main__":
    sys.exit(main())
