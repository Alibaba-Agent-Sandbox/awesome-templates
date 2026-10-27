#!/usr/bin/env python3
"""HTTP smoke and optional real coding acceptance against E2E_BASE_URL.

Use the public launch runner with --real-usage for owned provider acceptance.
This controller creates no sandbox and reads only target configuration booleans;
model credentials stay on the target server.
"""
from __future__ import annotations

import base64
import os
import shlex
import sys
import textwrap
import uuid

import httpx

# The host runner passes provider gateway authentication separately from app auth.
import json as _e2e_json
_GATEWAY_HEADERS = _e2e_json.loads(os.environ.get("E2E_GATEWAY_HEADERS_JSON", "{}"))
if not isinstance(_GATEWAY_HEADERS, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in _GATEWAY_HEADERS.items()):
    raise ValueError("E2E_GATEWAY_HEADERS_JSON must be an object of string headers")
_APPLICATION_HEADERS = {"Authorization": "Bearer " + os.environ["ABX_SERVER_TOKEN"]} if os.environ.get("ABX_SERVER_TOKEN") else {}

BASE_URL = os.environ.get("E2E_BASE_URL", "http://127.0.0.1:9000").rstrip("/")
WORK = os.environ.get("E2E_WORKSPACE") or os.environ.get("E2E_BASE_DIR") or "/home/user/workspace"
TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=30.0, pool=10.0)
LLM_TIMEOUT = float(os.environ.get("E2E_LLM_TIMEOUT", "420"))
RUN_LLM = os.environ.get("E2E_RUN_LLM", "").strip().lower()
REQUIRE = os.environ.get("E2E_REQUIRE_LLM", "").strip().lower() in {"1", "true", "yes"}
MODEL = os.environ.get("E2E_MODEL", "").strip()
MARKER = "ABX_E2E_OK"
PROBE_ROOT = os.path.join(WORK, "abx_e2e_codex_" + uuid.uuid4().hex)
BASELINE_SOURCE = "def fib(n):\n    return n\n"
ORIGINAL_TESTS = (
    "import unittest\nfrom fibonacci import fib\n"
    "class OriginalTests(unittest.TestCase):\n"
    "    def test_zero(self): self.assertEqual(fib(0), 0)\n"
    "    def test_existing_positive(self): self.assertEqual(fib(7), 13)\n"
)
COMMANDS = {
    "codex_version",
    "codex_setup_check",
    "codex_exec",
    "codex_config_write",
    "codex_agents_write",
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
    headers = dict(_APPLICATION_HEADERS)
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT, headers={**(headers), **_GATEWAY_HEADERS, **_APPLICATION_HEADERS}) as client:
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

    check("retired command absent", "codex" not in entries and
          client.post("/commands/codex", json={"prompt":"unused"}).status_code == 404)

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


def _trusted_verifier_source(task: str, ack: str, *, suites: bool) -> str:
    """Build an independent source verifier for an isolated Python process.

    The controller generates a new unpredictable ACK for EACH verifier call and
    accepts only HTTP200, exit0 and stdout.strip()==ACK. Never include the ACK in
    the model prompt. This is ordinary premature-exit protection, not a proof
    against arbitrary hostile code with the verifier's own OS authority.
    """
    prefix = '''
import contextlib, io, pathlib, sys, types, unittest
TASK = pathlib.Path(TASK_LITERAL)
ACK = ACK_LITERAL
# Import trusted stdlib above before adding the agent's directory. -I prevents
# cwd/user sitecustomize or an agent-written unittest.py at interpreter startup.
def load_source(name, path):
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    # Compile verified source bytes directly, avoiding agent-supplied .pyc files.
    exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    return module
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        sys.path.insert(0, str(TASK))
        fibonacci = load_source('fibonacci', TASK / 'fibonacci.py')
BODY
except BaseException:
    raise SystemExit(1)
print(ACK, flush=True)
'''.replace('TASK_LITERAL', repr(task)).replace('ACK_LITERAL', repr(ack))
    if suites:
        body = '''
original = load_source('test_original', TASK / 'test_original.py')
generated = load_source('test_fibonacci', TASK / 'test_fibonacci.py')
loader = unittest.TestLoader()
original_suite = loader.loadTestsFromModule(original)
generated_suite = loader.loadTestsFromModule(generated)
if original_suite.countTestCases() != 2 or generated_suite.countTestCases() < 1:
    raise AssertionError('test counts')
suite = unittest.TestSuite([original_suite, generated_suite])
result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
if (result.testsRun < 3 or not result.wasSuccessful() or result.skipped
        or result.expectedFailures or result.unexpectedSuccesses):
    raise AssertionError('tests did not all run successfully')
'''
    else:
        body = '''
fib = fibonacci.fib
if [fib(n) for n in (0,1,2,7,10)] != [0,1,1,13,55]:
    raise AssertionError('held-out results')
try:
    fib(-1)
except ValueError:
    pass
else:
    raise AssertionError('negative input')
'''
    return textwrap.dedent(prefix).replace('BODY', textwrap.indent(textwrap.dedent(body).strip(), '        '))

def _llm(client: httpx.Client, check) -> None:
    test = "codex_exec real coding task"
    forced_off = RUN_LLM in {"0", "false", "no"}
    enabled = RUN_LLM in {"1", "true", "yes"} or REQUIRE
    if REQUIRE and forced_off:
        check(test, False, "E2E_REQUIRE_LLM=1 conflicts with E2E_RUN_LLM=0")
        return
    if forced_off or not enabled:
        print(f"[SKIP] {test}", flush=True)
        if REQUIRE or RUN_LLM in {"1", "true", "yes"}:
            check(test, False, "model key or E2E_RUN_LLM is missing")
        return
    setup_response = client.post("/commands/codex_setup_check", json={})
    setup_body = setup_response.json() if setup_response.status_code == 200 else {}
    setup = setup_body.get("result", {})
    keys = setup.get("api_key_present", {}) if isinstance(setup, dict) else {}
    if not isinstance(keys, dict) or not any(
        keys.get(name) is True for name in ("OPENAI_API_KEY", "CODEX_API_KEY", "ABX_LLM_API_KEY")
    ):
        check(test, False, "target model configuration is unavailable")
        return
    task = os.path.join(PROBE_ROOT, "agent-task")
    shell_prefix = "env -i PATH=/usr/local/bin:/usr/bin:/bin python3 "
    seed = (
        "from pathlib import Path; r=Path(" + repr(task) + "); r.mkdir(parents=True); "
        "(r/'fibonacci.py').write_text(" + repr(BASELINE_SOURCE) + "); "
        "(r/'test_original.py').write_text(" + repr(ORIGINAL_TESTS) + ")"
    )
    seeded = client.post("/shell", json={
        "command": shell_prefix + "-c " + shlex.quote(seed), "cwd": WORK, "timeout": 30,
    })
    if seeded.status_code != 200 or seeded.json().get("exit_code") != 0:
        check("existing project seed", False)
        return
    baseline = client.post("/shell", json={
        "command": shell_prefix + "-m unittest -v test_original.py", "cwd": task, "timeout": 30,
    })
    baseline_body = baseline.json() if baseline.status_code == 200 else {}
    baseline_log = baseline_body.get("stderr", "")
    baseline_failed = baseline_body.get("exit_code") == 1 and all(
        expected in baseline_log for expected in (
            "FAIL: test_existing_positive", "Ran 2 tests", "FAILED (failures=1)",
        )
    ) and "ERROR:" not in baseline_log
    check("existing original tests fail before agent correction", baseline_failed)
    if not baseline_failed:
        return
    payload: dict = {
        "prompt": (
            "Fix the existing fibonacci.py implementing fib(n): fib(0)=0, fib(1)=1, "
            "and negative input raises ValueError. Preserve test_original.py byte for byte. "
            "Write REPORT.md explaining the correction and validation. Create test_fibonacci.py using "
            "stdlib unittest to cover zero, positive, and negative inputs. Run the "
            "tests with python3 -m unittest -v test_original.py test_fibonacci.py using your command "
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
            and _read_file(client, os.path.join(task, "fibonacci.py")) != BASELINE_SOURCE
            and _read_file(client, os.path.join(task, "test_original.py")) == ORIGINAL_TESTS
            and bool(_read_file(client, os.path.join(task, "REPORT.md")).strip())
            and bool(_read_file(client, os.path.join(task, "test_fibonacci.py")).strip())
        )
    except (httpx.HTTPError, KeyError, ValueError):
        files_ok = False
    check(test, response.status_code == 200 and completed and files_ok,
          f"HTTP {response.status_code} agent_tools={completed} artifacts={files_ok}")
    if response.status_code != 200 or not completed or not files_ok:
        return
    assertions_marker = "ABX_HELDOUT_" + uuid.uuid4().hex
    assertions = _trusted_verifier_source(task, assertions_marker, suites=False)
    # The completion marker is chosen only after the agent has exited. An
    # imported module calling sys.exit(0) or os._exit(0) cannot count as passing.
    verified = client.post("/shell", json={
        "command": shell_prefix + "-I -c " + shlex.quote(assertions), "cwd": task, "timeout": 30,
    })
    verified_body = verified.json() if verified.status_code == 200 else {}
    check("independent remote Fibonacci assertions", verified.status_code == 200
          and verified_body.get("exit_code") == 0
          and verified_body.get("stdout", "").strip() == assertions_marker)
    tests_marker = "ABX_TESTS_" + uuid.uuid4().hex
    test_runner = _trusted_verifier_source(task, tests_marker, suites=True)
    tests = client.post("/shell", json={
        "command": shell_prefix + "-I -c " + shlex.quote(test_runner), "cwd": task, "timeout": 30,
    })
    tests_body = tests.json() if tests.status_code == 200 else {}
    check("remote original and agent-written unittest rerun", tests.status_code == 200
          and tests_body.get("exit_code") == 0
          and tests_body.get("stdout", "").strip() == tests_marker)



if __name__ == "__main__":
    sys.exit(main())
