#!/usr/bin/env python3
"""Local HTTP smoke and opt-in real coding acceptance. No response-only L3 passes."""
from __future__ import annotations

import base64
import json
import os
import shlex
import sys
import textwrap
import uuid

import httpx

BASE_URL = os.environ.get("E2E_BASE_URL", "http://127.0.0.1:9000").rstrip("/")
BASE_DIR = os.environ.get("E2E_BASE_DIR", "/home/user").rstrip("/")
TOKEN = os.environ.get("E2E_TOKEN", "")
FAILED = 0


def enabled(name: str) -> bool:
    return os.environ.get(name, "").lower() in {"1", "true", "yes"}


def record(ok: bool, label: str) -> None:
    global FAILED
    FAILED += not ok
    print(f"[{'PASS' if ok else 'FAIL'}] {label}", flush=True)


def upload(client: httpx.Client, path: str, text: str) -> None:
    response = client.post("/files/upload-stream", json={"path": path, "content_base64": base64.b64encode(text.encode()).decode()})
    response.raise_for_status()


def read(client: httpx.Client, path: str) -> str:
    response = client.get("/files/download-stream", params={"path": path})
    response.raise_for_status()
    return base64.b64decode(response.json()["content_base64"]).decode()


def _verifier_source(project: str, ack: str, *, tests: bool) -> str:
    """Run with isolated Python; ACK is minted only after the model response.

    Direct source compilation and a fresh acknowledgment detect premature exit
    and stale bytecode. They are not an isolation boundary against hostile code
    with the same operating-system authority as the verifier.
    """
    prefix = """
import contextlib, io, pathlib, sys, types, unittest
PROJECT = pathlib.Path(PROJECT_LITERAL)
ACK = ACK_LITERAL
def load_source(name, path):
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    return module
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        sys.path.insert(0, str(PROJECT))
BODY
except BaseException:
    raise SystemExit(1)
print(ACK, flush=True)
""".replace("PROJECT_LITERAL", repr(project)).replace("ACK_LITERAL", repr(ack))
    if tests:
        body = """
load_source('calculator', PROJECT / 'calculator.py')
original = load_source('test_calculator', PROJECT / 'test_calculator.py')
suite = unittest.TestLoader().loadTestsFromModule(original)
if suite.countTestCases() != 3:
    raise AssertionError('original test count')
result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
if (result.testsRun != 3 or not result.wasSuccessful() or result.failures
        or result.errors or result.skipped or result.expectedFailures
        or result.unexpectedSuccesses):
    raise AssertionError('original tests did not all run successfully')
"""
    else:
        body = """
module = load_source('calculator_under_test', PROJECT / 'calculator.py')
if not all(module.add(a,b) == a+b for a,b in
           [(2,3),(-4,-3),(0,0),(127,83),(-91,13),(0.5,1.25)]):
    raise AssertionError('held-out results')
"""
    return textwrap.dedent(prefix).replace(
        "BODY", textwrap.indent(textwrap.dedent(body).strip(), "        ")
    )


def coding(client: httpx.Client, setup: dict | None = None) -> None:
    required = enabled("E2E_REQUIRE_LLM")
    forced_off = os.environ.get("E2E_RUN_LLM", "").lower() in {"0", "false", "no"}
    if forced_off:
        record(False, "required L3 must not skip model invocation") if required else print("[SKIP] L3 real coding; no acceptance claimed", flush=True)
        return
    if setup is None:
        response = client.post("/commands/qwen_setup_check", json={})
        candidate = response.json().get("result")
        if response.status_code != 200 or not isinstance(candidate, dict):
            record(False, "target setup inspection is required before model acceptance")
            return
        setup = candidate
    # The controller never needs the target's model credentials. Trust only the
    # read-only target diagnostic, not a similarly named local environment value.
    has_key = setup.get("api_key_set") is True
    if not has_key:
        if required or enabled("E2E_RUN_LLM"):
            record(False, "required L3 target has no compatible API key")
        else:
            print("[SKIP] L3 target has no compatible API key; no acceptance claimed", flush=True)
        return
    project = BASE_DIR + "/abx_e2e_qwen_" + uuid.uuid4().hex[:10]
    source = "def add(a, b):\n    return a - b\n"
    tests = ("import unittest\nfrom calculator import add\nclass AddTests(unittest.TestCase):\n"
             "    def test_positive(self): self.assertEqual(add(2, 3), 5)\n"
             "    def test_negative(self): self.assertEqual(add(-4, -3), -7)\n"
             "    def test_zero(self): self.assertEqual(add(0, 0), 0)\n")
    marker = "ABX_E2E_OK_" + uuid.uuid4().hex
    test_command = "env -i PATH=/usr/local/bin:/usr/bin:/bin python3 -I -c " + shlex.quote(
        "import sys,unittest;sys.path.insert(0,'.');"
        "result=unittest.TextTestRunner().run(unittest.defaultTestLoader.discover('.',pattern='test_calculator.py'));"
        "sys.exit(not result.wasSuccessful())"
    )
    try:
        upload(client, project + "/calculator.py", source)
        upload(client, project + "/test_calculator.py", tests)
        baseline = client.post("/shell", json={"command": test_command, "cwd": project, "timeout": 30})
        before = baseline.json()
        reproduced = (baseline.status_code == 200 and before.get("exit_code") == 1
                      and "AssertionError" in before.get("stderr", "")
                      and "Ran 3 tests" in before.get("stderr", ""))
        record(reproduced, "seeded source fails before model edits")
        if not reproduced:
            return
        prompt = ("In the current directory, fix calculator.py so add(a,b) adds numbers correctly. "
                  "Do not modify test_calculator.py. Create REPORT.md explaining the bug and fix. "
                  f"Create acceptance.txt containing exactly {marker} followed by a newline. "
                  "Run python3 -m unittest discover -v before finishing. Perform the file edits, do not just describe them.")
        payload = {"prompt": prompt, "max_turns": int(os.environ.get("E2E_MAX_TURNS", "20")),
                   "cwd": project, "yolo": True, "command_timeout": 300}
        if os.environ.get("E2E_MODEL"):
            payload["model"] = os.environ["E2E_MODEL"]
        response = client.post("/commands/qwen", json=payload, timeout=330)
        record(response.status_code == 200 and isinstance(response.json().get("result"), str), "real headless CLI completes")
        if response.status_code != 200:
            return
        updated = read(client, project + "/calculator.py")
        record(updated != source, "existing source changed via target files API")
        record(read(client, project + "/test_calculator.py") == tests, "original test file preserved")
        record(bool(read(client, project + "/REPORT.md").strip()), "new report artifact retrieved")
        record(read(client, project + "/acceptance.txt") == marker + "\n", "new exact artifact retrieved")
        # Mint independent completion ACKs after the model has returned. They
        # are never included in its prompt or accepted from model output.
        tests_ack = "ORIGINAL_TESTS_OK_" + uuid.uuid4().hex
        verify_tests = "env -i PATH=/usr/local/bin:/usr/bin:/bin python3 -I -c " + shlex.quote(
            _verifier_source(project, tests_ack, tests=True)
        )
        result = client.post("/shell", json={"command": verify_tests, "cwd": project, "timeout": 30})
        body = result.json()
        record(result.status_code == 200 and body.get("exit_code") == 0
               and body.get("stdout", "").strip() == tests_ack, "independent target unittest process passes")
        heldout_ack = "HELD_OUT_OK_" + uuid.uuid4().hex
        verify_heldout = "env -i PATH=/usr/local/bin:/usr/bin:/bin python3 -I -c " + shlex.quote(
            _verifier_source(project, heldout_ack, tests=False)
        )
        result = client.post("/shell", json={"command": verify_heldout, "cwd": project, "timeout": 30})
        body = result.json()
        record(result.status_code == 200 and body.get("exit_code") == 0
               and body.get("stdout", "").strip() == heldout_ack, "independent held-out calculations pass")
    except Exception as exc:
        record(False, f"L3 aborted ({type(exc).__name__}); response omitted")
    finally:
        result = client.delete("/files", params={"path": project})
        record(result.status_code in {200, 404}, "owned coding project cleanup")


def main() -> int:
    headers = {"X-Access-Token": TOKEN} if TOKEN else {}
    with httpx.Client(base_url=BASE_URL, headers=headers, timeout=60) as client:
        record(client.get("/health").status_code == 200, "health")
        response = client.get("/commands")
        entries = {c["name"]: c for c in response.json().get("commands", [])}
        record(response.status_code == 200 and {"qwen", "run", "qwen_version", "qwen_setup_check"} <= entries.keys(), "registered command names")
        types = {p["name"]: p["type"] for p in entries.get("qwen", {}).get("args", [])}
        record(types.get("max_turns") == "integer" and types.get("command_timeout") == "integer" and types.get("yolo") == "boolean", "typed command parameters")
        for payload in ({}, {"prompt": "x", "max_turns": "bad"}):
            record(client.post("/commands/qwen", json=payload).status_code == 400, "invalid arguments are HTTP 400")
        record(client.post("/commands/no_such_command", json={}).status_code == 404, "unknown command is HTTP 404")
        response = client.post("/commands/qwen_setup_check", json={})
        state = response.json().get("result", {})
        record(response.status_code == 200 and isinstance(state, dict), "read-only setup inspection")
        if state.get("installed"):
            record(client.post("/commands/qwen_version", json={}).json().get("result") == "0.23.0", "real CLI version equals pin")
        elif enabled("E2E_REQUIRE_CLI") or enabled("E2E_REQUIRE_LLM"):
            record(False, "required target CLI is installed")
        else:
            record(client.post("/commands/qwen_version", json={}).status_code == 500, "missing CLI has explicit execution error")
            print("[SKIP] real CLI version; no image/runtime acceptance claimed", flush=True)
        if not state.get("api_key_set"):
            response = client.post("/commands/qwen", json={"prompt": "test"})
            record(response.status_code == 500 and "required" in response.json().get("error", ""), "missing-key guard prevents OAuth login")
        coding(client, state)
    print(f"{FAILED} failed", flush=True)
    return int(bool(FAILED))


if __name__ == "__main__":
    sys.exit(main())
