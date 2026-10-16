#!/usr/bin/env python3
"""L0 HTTP smoke; E2E_RUN_LLM=1 enables strict real upstream L3 turns."""
import base64
import hashlib
import json
import os
import shlex
import sys
import time
import uuid

import httpx

BASE_URL = os.environ.get("E2E_BASE_URL", "http://127.0.0.1:9000").rstrip("/")

WORKSPACE = os.environ.get("E2E_WORKSPACE") or os.environ.get("E2E_BASE_DIR") or "/home/user/workspace"
BUGGY_SOURCE = "def normalize_usernames(values):\n    return sorted(set(values))\n"
REPORT_INPUT = [" Alice ", "BOB", "alice", "", " bob ", "CAROL"]
REPORT_OUTPUT = ["alice", "bob", "carol"]
# These fixed tests stay in the controller. The model cannot alter a remote
# test file because no copy of the tests is uploaded to its filesystem.
FIXED_TESTS = r"""
import sys
import types
import unittest
from pathlib import Path
path = Path(sys.argv[1]) / "normalizer.py"
module = types.ModuleType("target_normalizer")
exec(compile(path.read_text(), str(path), "exec"), module.__dict__)
class FixedAcceptance(unittest.TestCase):
    def test_case_and_whitespace(self):
        self.assertEqual(module.normalize_usernames([" Alice ", "BOB"]), ["alice", "bob"])
    def test_ordered_deduplication(self):
        self.assertEqual(module.normalize_usernames(["Zed", "amy", " ZED ", "AMY"]), ["zed", "amy"])
    def test_blanks(self):
        self.assertEqual(module.normalize_usernames(["", " ", "\t"]), [])
    def test_empty(self):
        self.assertEqual(module.normalize_usernames([]), [])
    def test_unicode(self):
        self.assertEqual(module.normalize_usernames(["Zoë", " ZOË "]), ["zoë"])
    def test_input_not_modified(self):
        values = [" A ", "a", " B "]
        before = values.copy()
        self.assertEqual(module.normalize_usernames(values), ["a", "b"])
        self.assertEqual(values, before)
unittest.main(argv=["controller-fixed-tests"], verbosity=2)
"""


def _headers() -> dict:
    token = os.environ.get("E2E_TOKEN") or os.environ.get("ABX_SERVER_TOKEN", "")
    return {"X-Access-Token": token} if token else {}


def _read_file(client: httpx.Client, path: str) -> str:
    response = client.get("/files/download-stream", params={"path": path})
    response.raise_for_status()
    return base64.b64decode(response.json()["content_base64"]).decode("utf-8")


def _fixed_tests(client: httpx.Client, task: str) -> dict:
    command = "env -i PATH=/usr/local/bin:/usr/bin:/bin python3 -I -c " + shlex.quote(FIXED_TESTS) + " " + shlex.quote(task)
    response = client.post("/shell", json={"command": command, "cwd": task, "timeout": 30})
    response.raise_for_status()
    return response.json()


def _agent_message(items: list, marker: str) -> bool:
    return any(isinstance(event, dict) and isinstance(event.get("item"), dict)
               and event["item"].get("type") == "agent_message"
               and event["item"].get("text", "").strip() == marker for event in items)


def _has_command(items: list) -> bool:
    return any(isinstance(event, dict) and event.get("type") == "item.completed"
               and isinstance(event.get("item"), dict)
               and event["item"].get("type") == "command_execution"
               and event["item"].get("status") == "completed"
               and event["item"].get("exit_code") == 0 for event in items)


def _artifact(client: httpx.Client, session_id: str, relative: str) -> str:
    identifier = base64.urlsafe_b64encode(relative.encode()).decode().rstrip("=")
    response = client.get(f"/v1/agents/sessions/{session_id}/artifacts/{identifier}")
    response.raise_for_status()
    return response.json()["content"]


def _coding_acceptance(client: httpx.Client, check) -> None:
    run = os.environ.get("E2E_RUN_LLM", "").strip().lower()
    require = os.environ.get("E2E_REQUIRE_LLM", "").strip().lower() in {"1", "true", "yes"}
    if require and run in {"0", "false", "no"}:
        check("L3 real coding task required", False)
        return
    if not require and run not in {"1", "true", "yes"}:
        print("[SKIP] L3 real coding task: set E2E_RUN_LLM=1 or E2E_REQUIRE_LLM=1", flush=True)
        return
    # Credentials belong to the remote server. The controller need not receive
    # a model key; explicit L3 requests fail on upstream errors rather than SKIP.
    task_name = "abx_e2e_codex_api_" + uuid.uuid4().hex
    task = os.path.join(WORKSPACE, task_name)
    source = os.path.join(task, "normalizer.py")
    report_path = os.path.join(task, "normalization-report.json")
    live_id = ""
    try:
        response = client.post("/files/upload-stream", json={"path": source,
            "content_base64": base64.b64encode(BUGGY_SOURCE.encode()).decode()})
        response.raise_for_status()
        baseline = _fixed_tests(client, task)
        baseline_ok = baseline.get("exit_code") == 1 and "Ran 6 tests" in baseline.get("stderr", "") and "FAILED" in baseline.get("stderr", "")
        check("L3 existing source reproduces fixed-test failures", baseline_ok)
        if not baseline_ok:
            return
        model = os.environ.get("E2E_MODEL") or os.environ.get("CODEX_MODEL") or os.environ.get("ABX_LLM_MODEL", "")
        prompt = (
            f"Work only in {task}. Fix the EXISTING normalizer.py normalize_usernames(values) function. "
            "Strip whitespace and lowercase every username, drop blank usernames, deduplicate "
            "while preserving first-seen order, support Unicode lowercase, and do not mutate the input list. "
            "Use your command tool to exercise the function. Do not create or edit any test files: "
            "the controller owns fixed independent tests outside your filesystem. "
            f"Create normalization-report.json as a JSON object with input={json.dumps(REPORT_INPUT)} "
            f"and output={json.dumps(REPORT_OUTPUT)} by actually calling the fixed function. "
            "After the source is fixed and the report exists, reply with exactly ABX_E2E_OK."
        )
        response = client.post("/v1/agents/sessions", json={"agent": {"model": model,
            "instructions": "Complete the requested coding task using upstream Codex tools."},
            "input": prompt, "background": True})
        response.raise_for_status()
        live_id = response.json()["id"]
        deadline = time.monotonic() + float(os.environ.get("E2E_LLM_TIMEOUT", "330"))
        result = response.json()
        while time.monotonic() < deadline:
            result = client.get(f"/v1/agents/sessions/{live_id}").raise_for_status().json()
            if result["status"] != "in_progress":
                break
            time.sleep(0.25)
        items = client.get(f"/v1/agents/sessions/{live_id}/items").raise_for_status().json()["data"]
        completed = result["status"] == "idle" and _agent_message(items, "ABX_E2E_OK") and _has_command(items)
        check("L3 real upstream background coding completion", completed)
        if not completed:
            return
        changed_source = _read_file(client, source)
        check("L3 existing source changed on target", changed_source != BUGGY_SOURCE and bool(changed_source.strip()))
        report = _read_file(client, report_path)
        report_ok = json.loads(report) == {"input": REPORT_INPUT, "output": REPORT_OUTPUT}
        check("L3 independent new report contents", report_ok)
        check("L3 artifact API matches remote report", _artifact(client, live_id, task_name + "/normalization-report.json") == report)
        rerun = _fixed_tests(client, task)
        tests_ok = rerun.get("exit_code") == 0 and "Ran 6 tests" in rerun.get("stderr", "") and "OK" in rerun.get("stderr", "")
        check("L3 controller-owned fixed tests pass on target", tests_ok)
        if not tests_ok or not report_ok or changed_source == BUGGY_SOURCE:
            return
        prompt = (
            f"Continue the same task in {task}. Read normalization-report.json; create "
            "resume-summary.json containing only report_sha256 (the SHA-256 of that report's actual bytes) "
            "and normalized_count (length of its output list). Use your command tool. "
            "Do not modify normalizer.py or normalization-report.json. Reply with exactly ABX_RESUME_OK."
        )
        with client.stream("POST", f"/v1/agents/sessions/{live_id}/events", json={"input": prompt, "stream": True}) as response:
            response.raise_for_status()
            body = response.read().decode()
        stream_items = []
        for line in body.splitlines():
            if line.startswith("data:"):
                event = json.loads(line[5:].strip())
                if isinstance(event, dict):
                    stream_items.append(event)
        check("L3 exact-thread resume SSE completion", _agent_message(stream_items, "ABX_RESUME_OK")
              and any(e.get("type") == "agent.session.turn.completed" for e in stream_items)
              and not any("failed" in e.get("type", "") for e in stream_items))
        summary = json.loads(_artifact(client, live_id, task_name + "/resume-summary.json"))
        check("L3 independently verified resume artifact", summary == {
            "report_sha256": hashlib.sha256(report.encode()).hexdigest(), "normalized_count": len(REPORT_OUTPUT)})
        check("L3 resume preserves fixed source and first artifact",
              _read_file(client, source) == changed_source and _read_file(client, report_path) == report)
        final_tests = _fixed_tests(client, task)
        check("L3 final independent fixed-test rerun", final_tests.get("exit_code") == 0
              and "Ran 6 tests" in final_tests.get("stderr", "") and "OK" in final_tests.get("stderr", ""))
    except (httpx.HTTPError, KeyError, ValueError, TypeError):
        check("L3 coding request/schema/artifact verification", False)
    finally:
        if live_id:
            response = client.delete(f"/v1/agents/sessions/{live_id}")
            check("L3 owned session cleanup", response.status_code in (200, 404))
        response = client.delete("/files", params={"path": task})
        check("L3 owned coding project cleanup", response.status_code in (200, 404))


def main() -> int:
    failures = 0
    def check(label, ok):
        nonlocal failures
        print(f"[{'PASS' if ok else 'FAIL'}] {label}", flush=True)
        failures += not ok

    headers = _headers()
    with httpx.Client(base_url=BASE_URL, timeout=360, headers=headers) as client:
        health = client.get("/health")
        check("health", health.status_code == 200 and health.json().get("status") == "ok")
        response = client.get("/commands")
        names = {entry["name"] for entry in response.json().get("commands", [])}
        check("named command discovery", {"codex", "codex_version", "agent_status"} <= names)
        created = client.post("/v1/agents", json={"model": "test-model", "instructions": "Be concise", "name": "smoke"})
        check("create saved agent", created.status_code == 200 and created.json().get("object") == "agent")
        agent_id = created.json()["id"]
        check("list saved agents", agent_id in {a["id"] for a in client.get("/v1/agents").json()["data"]})
        check("update saved agent", client.post(f"/v1/agents/{agent_id}", json={"name": "updated"}).json().get("name") == "updated")
        response = client.post("/v1/agents/sessions", json={"agent": agent_id})
        session_id = response.json()["id"]
        check("create session from saved agent", response.status_code == 200 and response.json().get("model") == "test-model")
        check("get session", client.get(f"/v1/agents/sessions/{session_id}").json().get("status") == "idle")
        check("update session", client.post(f"/v1/agents/sessions/{session_id}", json={"instructions": "Updated"}).json().get("instructions") == "Updated")
        check("list sessions", session_id in {s["id"] for s in client.get("/v1/agents/sessions").json()["data"]})
        check("empty items", client.get(f"/v1/agents/sessions/{session_id}/items").json().get("data") == [])
        check("missing input rejected", client.post(f"/v1/agents/sessions/{session_id}/events", json={}).status_code == 400)
        check("mistyped stream rejected", client.post("/v1/agents/sessions", json={"stream": "true"}).status_code == 400)
        check("unsupported tool rejected", client.post("/v1/agents", json={"tools": [{"type": "function"}]}).status_code == 400)
        check("secret artifact denied", client.get(f"/v1/agents/sessions/{session_id}/artifacts/LmVudg").status_code == 403)
        check("idle event subscription", client.get(f"/v1/agents/sessions/{session_id}/events").json().get("status") == "idle")
        check("delete session", client.delete(f"/v1/agents/sessions/{session_id}").json().get("deleted") is True)
        check("deleted session missing", client.get(f"/v1/agents/sessions/{session_id}").status_code == 404)
        check("delete saved agent", client.delete(f"/v1/agents/{agent_id}").json().get("deleted") is True)
        _coding_acceptance(client, check)
    return int(bool(failures))


if __name__ == "__main__":
    sys.exit(main())
