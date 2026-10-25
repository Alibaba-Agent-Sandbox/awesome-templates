#!/usr/bin/env python3
"""Validate the actual HTTP target; L3 requires remote files and independent tests."""
from __future__ import annotations

import base64
import os
import shlex
import sys
import uuid

import httpx

BASE_URL = os.environ.get("E2E_BASE_URL", "http://127.0.0.1:9000").rstrip("/")
WORKSPACE = os.environ.get("E2E_WORKSPACE", "/home/user/app").rstrip("/")
RUN_LLM = os.environ.get("E2E_RUN_LLM", "0").strip().lower()
REQUIRE = os.environ.get("E2E_REQUIRE_LLM", "0").strip().lower() in {"1", "true", "yes"}
PINNED = "0.241.1"
RESULTS: list[tuple[str, str]] = []


def record(ok: bool, test: str) -> None:
    status = "PASS" if ok else "FAIL"
    RESULTS.append((status, test))
    # Never log response bodies, argv, prompts, environment values or exception text.
    print(f"[{status}] {test}", flush=True)


def check_model_call(client: httpx.Client, setup: dict) -> None:
    enabled = RUN_LLM in {"1", "true", "yes"}
    if not enabled:
        if REQUIRE:
            record(False, "L3 requires E2E_RUN_LLM=1")
        else:
            print("[NOT RUN] L3 disabled by E2E_RUN_LLM", flush=True)
        return
    if setup.get("api_key_set") is not True:
        response = client.post("/commands/droid", json={"prompt": "Do not start interactive login"})
        record(response.status_code == 500 and "FACTORY_API_KEY is required" in
               response.json().get("error", ""), "target missing-key guard fails without interactive login")
        record(False, "L3 blocked: target FACTORY_API_KEY is missing")
        return
    marker = "ABX_E2E_" + uuid.uuid4().hex
    project = WORKSPACE + "/abx_e2e_droid_" + uuid.uuid4().hex
    source = "def add(a, b):\n    return a - b\n"
    tests = (
        "import unittest\nfrom calc import add\n"
        "class TestAdd(unittest.TestCase):\n"
        "    def test_positive(self): self.assertEqual(add(2, 3), 5)\n"
        "    def test_negative(self): self.assertEqual(add(-2, -3), -5)\n"
        "    def test_zero(self): self.assertEqual(add(0, 0), 0)\n"
        "if __name__ == '__main__': unittest.main()\n"
    )
    test_command = "env -i PATH=/usr/local/bin:/usr/bin:/bin python3 -I -c " + shlex.quote(
        "import sys,unittest;sys.path.insert(0,'.');"
        "result=unittest.TextTestRunner().run(unittest.defaultTestLoader.discover('.',pattern='test_calc.py'));"
        "sys.exit(not result.wasSuccessful())"
    )
    try:
        for name, content in (("calc.py", source), ("test_calc.py", tests)):
            client.post("/files/upload-stream", json={
                "path": project + "/" + name,
                "content_base64": base64.b64encode(content.encode()).decode(),
            }).raise_for_status()
        before = client.post("/shell", json={"command": test_command, "cwd": project, "timeout": 30})
        baseline = before.json()
        reproduced = (before.status_code == 200 and baseline.get("exit_code") == 1
                      and "AssertionError" in baseline.get("stderr", "")
                      and "Ran 3 tests" in baseline.get("stderr", ""))
        record(reproduced, "L3 seeded source reproduces failing independent tests")
        if not reproduced:
            return
        response = client.post("/commands/droid", json={
            "prompt": (
                "Fix existing calc.py so add(a, b) returns their sum. Do not modify test_calc.py. "
                "Create report.txt describing the source change. "
                f"Create acceptance.txt containing exactly {marker} followed by a newline. "
                f"After completing the task, reply with {marker}."
            ),
            "cwd": project, "auto": "low", "command_timeout": 300,
        }, timeout=float(os.environ.get("E2E_LLM_TIMEOUT", "360")))
        result = response.json().get("result")
        responded = response.status_code == 200 and isinstance(result, str) and marker in result
        record(responded, "L3 headless coding request completes")
        if not responded:
            return

        def read_file(name: str) -> str:
            artifact = client.get("/files/download-stream", params={"path": project + "/" + name})
            artifact.raise_for_status()
            return base64.b64decode(artifact.json()["content_base64"]).decode()

        record(read_file("calc.py") != source, "L3 existing source modified on target")
        record(read_file("test_calc.py") == tests, "L3 original independent tests preserved")
        record(bool(read_file("report.txt").strip()) and read_file("acceptance.txt") == marker + "\n",
               "L3 new artifacts downloaded from target")
        after = client.post("/shell", json={"command": test_command, "cwd": project, "timeout": 30})
        checked = after.json()
        record(after.status_code == 200 and checked.get("exit_code") == 0
               and "Ran 3 tests" in checked.get("stderr", ""), "L3 independent target test rerun passes")
        heldout = (
            "import importlib.util;"
            f"spec=importlib.util.spec_from_file_location('calc_under_test',{project + '/calc.py'!r});"
            "module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);"
            "assert all(module.add(a,b)==a+b for a,b in [(2,3),(-2,-3),(0,0),(99,101),(-7,4),(8,-3),(0,12)])\n"
            "print('INDEPENDENT_OK')\n"
        )
        response = client.post("/shell", json={
            "command": "env -i PATH=/usr/local/bin:/usr/bin:/bin python3 -I -c " + shlex.quote(heldout),
            "cwd": project, "timeout": 30,
        })
        checked = response.json()
        record(response.status_code == 200 and checked.get("exit_code") == 0
               and checked.get("stdout", "").strip() == "INDEPENDENT_OK",
               "L3 held-out target assertions pass independently")
    except Exception as exc:
        print(f"[FAIL] L3 aborted ({type(exc).__name__}); content omitted", flush=True)
        record(False, "L3 coding acceptance completes")
    finally:
        cleanup = client.delete("/files", params={"path": project})
        record(cleanup.status_code in {200, 404}, "L3 owned project cleanup")


def main() -> int:
    token = os.environ.get("ABX_SERVER_TOKEN", "")
    headers = {"Authorization": "Bearer " + token} if token else {}
    with httpx.Client(base_url=BASE_URL, headers=headers, timeout=40) as client:
        health = client.get("/health")
        record(health.status_code == 200 and health.json().get("status") == "ok", "target health")
        listed = client.get("/commands")
        entries = listed.json().get("commands", [])
        names = {entry.get("name") for entry in entries}
        signature = next((entry for entry in entries if entry.get("name") == "droid"), {})
        params = {arg.get("name"): arg for arg in signature.get("args", [])}
        record(listed.status_code == 200 and {"droid", "droid_version", "droid_setup_check"} <= names
               and {"prompt", "auto", "cwd", "command_timeout"} <= params.keys()
               and params["prompt"].get("required") is True
               and params["command_timeout"].get("type") == "integer", "target command signatures")
        record(client.post("/commands/droid", json={}).status_code == 400, "missing required prompt returns 400")
        record(client.post("/commands/no_such_command", json={}).status_code == 404, "unknown command returns 404")
        for args in ({"prompt": "  "}, {"prompt": "x", "command_timeout": 0}, {"prompt": "x", "auto": "unsafe"}):
            record(client.post("/commands/droid", json=args).status_code == 500,
                   "invalid command values fail before upstream execution")
        version = client.post("/commands/droid_version", json={})
        record(version.status_code == 200 and version.json().get("result") == PINNED, "actual target version matches pin")
        response = client.post("/commands/droid_setup_check", json={})
        setup = response.json().get("result", {})
        valid = (response.status_code == 200 and setup.get("installed") is True
                 and setup.get("package") == "@factory/cli" and setup.get("version") == PINNED
                 and setup.get("expected_version") == PINNED and setup.get("workspace_exists") is True
                 and isinstance(setup.get("api_key_set"), bool) and setup.get("auto_update_enabled") is False)
        record(valid, "actual target setup inspection")
        if valid:
            check_model_call(client, setup)
    return int(any(status == "FAIL" for status, _ in RESULTS))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"[FAIL] HTTP acceptance aborted ({type(exc).__name__}); content omitted", flush=True)
        sys.exit(1)
