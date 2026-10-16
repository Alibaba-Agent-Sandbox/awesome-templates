#!/usr/bin/env python3
"""Check the actual HTTP target. Core CLI/serve failures never become skips.

L0 deliberately omits the paid model call with E2E_RUN_LLM=0. L3 requires
E2E_REQUIRE_LLM=1 and requires editing existing code, new artifacts, and independent remote tests.
The tester does not inspect its own CLI installation or model credentials.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import shlex
import sys
import textwrap
import uuid

import httpx

BASE_URL = os.environ.get("E2E_BASE_URL", "http://127.0.0.1:9000").rstrip("/")
WORKSPACE = os.environ.get("E2E_WORKSPACE", "/home/user/app").rstrip("/")
RUN_LLM = os.environ.get("E2E_RUN_LLM", "0").strip().lower()
REQUIRE = os.environ.get("E2E_REQUIRE_LLM", "0").strip().lower() in {"1", "true", "yes"}
PINNED = "1.19.0"
REQUIRED = {"opencode", "opencode_run", "opencode_version", "opencode_setup_check",
            "opencode_serve_start", "opencode_serve_status", "opencode_serve_stop"}
RUN_PARAMS = {"prompt", "model", "agent", "session", "continue_session", "cwd"}
RESULTS: list[tuple[str, str]] = []


def record(ok: bool, test: str) -> None:
    status = "PASS" if ok else "FAIL"
    RESULTS.append((status, test))
    # No response bodies, prompts, command arguments or exception messages in logs.
    print(f"[{status}] {test}", flush=True)


def check_code_artifact(client: httpx.Client) -> None:
    path = WORKSPACE + "/e2e_opencode_code_" + uuid.uuid4().hex + ".txt"
    marker = "REMOTE_CODE_" + uuid.uuid4().hex
    try:
        code = f"from pathlib import Path\nPath({path!r}).write_text({marker!r})\nprint('CODE_OK')"
        response = client.post("/shell", json={"command": "python3 -c " + shlex.quote(code)})
        record(response.status_code == 200 and response.json().get("exit_code") == 0
               and response.json().get("stdout", "").strip() == "CODE_OK", "actual target Python execution")
        artifact = client.get("/files/download-stream", params={"path": path})
        data = base64.b64decode(artifact.json().get("content_base64", ""))
        record(artifact.status_code == 200 and data == marker.encode(), "target code artifact downloaded via files API")
    finally:
        deleted = client.delete("/files", params={"path": path})
        record(deleted.status_code in {200, 404}, "owned code artifact cleanup")


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
load_source('calc', PROJECT / 'calc.py')
original = load_source('test_calc', PROJECT / 'test_calc.py')
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
module = load_source('calc_under_test', PROJECT / 'calc.py')
if not all(module.add(a,b) == a+b for a,b in
           [(2,3),(-2,-3),(0,0),(8,-3),(-7,4),(99,101),(0,12),
            (1543,-271),(0,98765),(-809,611),(0.5,1.25)]):
    raise AssertionError('held-out results')
"""
    return textwrap.dedent(prefix).replace(
        "BODY", textwrap.indent(textwrap.dedent(body).strip(), "        ")
    )


def check_model_call(client: httpx.Client) -> None:
    enabled = RUN_LLM in {"1", "true", "yes"}
    if not enabled:
        if REQUIRE:
            record(False, "L3 requires E2E_RUN_LLM=1")
        else:
            print("[NOT RUN] L3 model/artifact acceptance; use E2E_RUN_LLM=1 E2E_REQUIRE_LLM=1", flush=True)
        return
    marker = "ABX_E2E_" + uuid.uuid4().hex
    project = WORKSPACE + "/abx_e2e_opencode_" + uuid.uuid4().hex
    source = "def add(a, b):\n    return a - b\n"
    fixed_tests = (
        "import unittest\nfrom calc import add\n"
        "class TestAdd(unittest.TestCase):\n"
        "    def test_positive(self): self.assertEqual(add(2, 3), 5)\n"
        "    def test_negative(self): self.assertEqual(add(-2, -3), -5)\n"
        "    def test_zero(self): self.assertEqual(add(0, 0), 0)\n"
        "if __name__ == '__main__': unittest.main()\n"
    )
    # /shell accepts argv via shlex.split, so cwd is an API parameter and
    # shell operators must not be used. No client-local filesystem inspection.
    test_command = "env -i PATH=/usr/local/bin:/usr/bin:/bin python3 -m unittest -v test_calc.py"
    try:
        for name, content in (("calc.py", source), ("test_calc.py", fixed_tests)):
            uploaded = client.post("/files/upload-stream", json={
                "path": project + "/" + name,
                "content_base64": base64.b64encode(content.encode()).decode(),
            })
            uploaded.raise_for_status()
        before = client.post("/shell", json={"command": test_command, "cwd": project, "timeout": 30})
        baseline = before.json()
        reproduced = (before.status_code == 200 and baseline.get("exit_code") == 1
                      and "AssertionError" in baseline.get("stderr", "")
                      and "Ran 3 tests" in baseline.get("stderr", ""))
        record(reproduced, "L3 seeded existing source reproduces failing independent tests")
        if not reproduced:
            return
        response = client.post("/commands/opencode_run", json={
            "prompt": (
                "Fix the existing calc.py so add(a, b) returns their sum. Do not modify test_calc.py. "
                "Run python3 -m unittest -v test_calc.py and make all three tests pass. "
                "Create report.txt describing the source change and the test result. "
                f"Create acceptance.txt containing exactly {marker} followed by a newline. "
                f"After completing the task, reply with exactly {marker}."
            ),
            "cwd": project,
        }, timeout=float(os.environ.get("E2E_LLM_TIMEOUT", "600")))
        result = response.json().get("result", {})
        responded = (response.status_code == 200 and isinstance(result, dict)
                     and result.get("text", "").strip() == marker
                     and isinstance(result.get("session_id"), str) and bool(result.get("session_id")))
        record(responded, "L3 real headless coding response and session")
        if not responded:
            return

        def read_file(name: str) -> str:
            artifact = client.get("/files/download-stream", params={"path": project + "/" + name})
            artifact.raise_for_status()
            return base64.b64decode(artifact.json()["content_base64"]).decode()

        modified = read_file("calc.py")
        preserved_tests = read_file("test_calc.py")
        report = read_file("report.txt")
        acceptance = read_file("acceptance.txt")
        changed = modified != source
        preserved = preserved_tests == fixed_tests
        artifacts_ok = bool(report.strip()) and acceptance == marker + "\n"
        record(changed, "L3 existing source was modified on target")
        record(preserved, "L3 seeded independent tests were preserved")
        record(artifacts_ok,
               "L3 new agent report and exact artifact downloaded from target")
        tests_ack = "ORIGINAL_TESTS_OK_" + uuid.uuid4().hex
        after = client.post("/shell", json={
            "command": "env -i PATH=/usr/local/bin:/usr/bin:/bin python3 -I -c " + shlex.quote(
                _verifier_source(project, tests_ack, tests=True)),
            "cwd": project, "timeout": 30})
        tests = after.json()
        tests_ok = (after.status_code == 200 and tests.get("exit_code") == 0
                    and tests.get("stdout", "").strip() == tests_ack)
        record(tests_ok, "L3 independent remote fixed-test rerun passes")
        # Additional held-out cases are supplied only after the agent finishes.
        heldout_ack = "INDEPENDENT_OK_" + uuid.uuid4().hex
        assertions = _verifier_source(project, heldout_ack, tests=False)
        independent = client.post("/shell", json={
            "command": "env -i PATH=/usr/local/bin:/usr/bin:/bin python3 -I -c " + shlex.quote(assertions),
            "cwd": project, "timeout": 30,
        })
        checked = independent.json()
        independent_ok = (independent.status_code == 200 and checked.get("exit_code") == 0
                          and checked.get("stdout", "").strip() == heldout_ack)
        record(independent_ok,
               "L3 independent remote held-out assertions pass")
        if not all((changed, preserved, artifacts_ok, tests_ok, independent_ok)):
            return

        # This is an explicit continuation of the exact session returned above,
        # never global --continue. Expected hashes/results stay on the controller.
        missing = client.get("/files/download-stream", params={"path": project + "/resume.json"})
        record(missing.status_code == 404, "L3 resume artifact absent before exact-session turn")
        if missing.status_code != 404:
            return
        session_id = result["session_id"]
        resume_marker = "ABX_RESUME_" + uuid.uuid4().hex
        resume_pairs = [(1543, -271), (0, 98765), (-809, 611)]
        expected_resume = {
            "report_sha256": hashlib.sha256(report.encode()).hexdigest(),
            "results": [{"a": a, "b": b, "sum": a + b} for a, b in resume_pairs],
        }
        resumed = client.post("/commands/opencode_run", json={
            "session": session_id,
            "cwd": project,
            "prompt": (
                "Continue this exact session in its existing project. Read report.txt and calc.py. "
                "Do not modify calc.py, test_calc.py, report.txt, or acceptance.txt. "
                "Using the actual report.txt bytes, compute its SHA-256 with hashlib. "
                "Import add from the existing calc.py and call it for these ordered (a, b) pairs: "
                f"{json.dumps(resume_pairs)}. Create a new resume.json object with exactly two keys: "
                "report_sha256 (the lowercase SHA-256 hex digest) and results (an ordered list of "
                "objects with a, b, and sum from the actual add calls). Do not guess the hash or results. "
                f"After writing resume.json, reply with exactly {resume_marker}."
            ),
        }, timeout=float(os.environ.get("E2E_LLM_TIMEOUT", "600")))
        resumed_result = resumed.json().get("result", {})
        resumed_ok = (resumed.status_code == 200 and isinstance(resumed_result, dict)
                      and resumed_result.get("text", "").strip() == resume_marker
                      and resumed_result.get("session_id") == session_id)
        record(resumed_ok, "L3 exact-session resume response preserves the returned session id")
        if not resumed_ok:
            return
        try:
            resume_artifact = json.loads(read_file("resume.json"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            resume_artifact = None
        record(json.dumps(resume_artifact, sort_keys=True) == json.dumps(expected_resume, sort_keys=True),
               "L3 resume artifact independently matches original report SHA-256 and held-out calculations")
        record(read_file("calc.py") == modified and read_file("test_calc.py") == preserved_tests
               and read_file("report.txt") == report and read_file("acceptance.txt") == acceptance,
               "L3 resume preserves original source tests report and acceptance artifact")
        resume_ack = "RESUME_INDEPENDENT_OK_" + uuid.uuid4().hex
        resume_assertions = _verifier_source(project, resume_ack, tests=False)
        repeated = client.post("/shell", json={
            "command": "env -i PATH=/usr/local/bin:/usr/bin:/bin python3 -I -c " + shlex.quote(resume_assertions),
            "cwd": project, "timeout": 30,
        })
        repeated_result = repeated.json()
        record(repeated.status_code == 200 and repeated_result.get("exit_code") == 0
               and repeated_result.get("stdout", "").strip() == resume_ack,
               "L3 independent remote held-out assertions pass after exact-session resume")
    except Exception as exc:
        print(f"[FAIL] L3 coding acceptance aborted ({type(exc).__name__}); response content omitted", flush=True)
        record(False, "L3 real coding acceptance completed")
    finally:
        deleted = client.delete("/files", params={"path": project})
        record(deleted.status_code in {200, 404}, "L3 owned coding project cleanup")


def main() -> int:
    headers = {}
    token = os.environ.get("E2E_TOKEN") or os.environ.get("ABX_SERVER_TOKEN", "")
    if token:
        headers["Authorization"] = "Bearer " + token
    with httpx.Client(base_url=BASE_URL, headers=headers, timeout=40) as client:
        health = client.get("/health")
        record(health.status_code == 200 and health.json().get("status") == "ok", "target health")
        commands = client.get("/commands")
        entries = commands.json().get("commands", [])
        names = {entry.get("name") for entry in entries}
        run = next((entry for entry in entries if entry.get("name") == "opencode_run"), {})
        params = {arg.get("name") for arg in run.get("args", [])}
        record(commands.status_code == 200 and REQUIRED <= names and RUN_PARAMS <= params,
               "target command registration and parameters")
        missing = client.post("/commands/opencode_run", json={})
        record(missing.status_code == 400, "missing required prompt returns 400")
        invalid = client.post("/commands/opencode_run", json={"prompt": "  "})
        record(invalid.status_code == 500, "empty prompt fails before CLI execution")
        unknown = client.post("/commands/no_such_command", json={})
        record(unknown.status_code == 404, "unknown command returns 404")
        check_code_artifact(client)
        version = client.post("/commands/opencode_version", json={})
        record(version.status_code == 200 and version.json().get("result") == PINNED,
               "required target CLI version matches pin")
        setup = client.post("/commands/opencode_setup_check", json={})
        record(setup.status_code == 200 and setup.json().get("result") == "ok",
               "required target setup check")
        try:
            started = client.post("/commands/opencode_serve_start", json={"port": 4096, "hostname": "0.0.0.0"})
            state = started.json().get("result", {})
            record(started.status_code == 200 and state.get("running") is True
                   and state.get("healthy") is True and state.get("version") == PINNED
                   and state.get("port") == 4096, "target serve startup and target-side authenticated health/version")
            status = client.post("/commands/opencode_serve_status", json={})
            state = status.json().get("result", {})
            record(status.status_code == 200 and state.get("running") is True and state.get("version") == PINNED,
                   "target serve status")
            again = client.post("/commands/opencode_serve_start", json={"port": 4096, "hostname": "0.0.0.0"})
            record(again.status_code == 200 and again.json().get("result", {}).get("pid") == state.get("pid"),
                   "target serve start is idempotent")
        finally:
            stopped = client.post("/commands/opencode_serve_stop", json={})
            record(stopped.status_code == 200 and stopped.json().get("result") == "stopped", "target serve stop")
            status = client.post("/commands/opencode_serve_status", json={})
            record(status.status_code == 200 and status.json().get("result", {}).get("running") is False,
                   "target serve stopped state")
        check_model_call(client)
    failed = sum(status == "FAIL" for status, _ in RESULTS)
    print(f"SUMMARY {len(RESULTS) - failed} PASS, {failed} FAIL, 0 SKIP (L3 status printed separately)", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"[FAIL] acceptance aborted ({type(exc).__name__}); response content omitted", flush=True)
        sys.exit(1)
