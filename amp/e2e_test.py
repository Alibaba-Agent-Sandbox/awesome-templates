#!/usr/bin/env python3
"""Local smoke for the amp template against E2E_BASE_URL.

Express runs go through scripts/express_e2e.py (CLI and SDK). This file is
the no-cloud check. A live ``amp -x`` call is SKIP unless AMP_API_KEY is set
and E2E_RUN_LLM is not 0. L3 additionally requires changed source, downloaded
artifacts, preserved tests, and independently executed target-side tests.
"""
from __future__ import annotations

import base64
import json
import os
import shlex
import sys
import uuid

import httpx

BASE_URL = os.environ.get("E2E_BASE_URL", "http://127.0.0.1:9000").rstrip("/")
PINNED_VERSION = "0.0.1792022479-ge66e24"
MARKER = "ABX_E2E_OK"
TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=10.0)
TOKEN = os.environ.get("E2E_TOKEN", "")
LLM_TIMEOUT = float(os.environ.get("E2E_LLM_TIMEOUT", "600"))
RUN_LLM = os.environ.get("E2E_RUN_LLM", "").strip().lower()
REQUIRE = os.environ.get("E2E_REQUIRE_LLM", "").strip().lower() in {"1", "true", "yes"}
NAMES = {"amp_version", "amp_setup_check", "amp_execute", "amp"}

RESULTS: list[tuple[str, str, str]] = []


def record(status: str, test: str, detail: str = "") -> None:
    RESULTS.append((status, test, detail))
    line = f"[{status}] {test}"
    if detail:
        line += f" — {detail}"
    print(line, flush=True)


def _short(value: object, limit: int = 240) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def main() -> int:
    failures = 0
    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT, headers=headers) as client:
        health = client.get("/health")
        ok = health.status_code == 200 and health.json().get("status") == "ok"
        record("PASS" if ok else "FAIL", "GET /health", f"HTTP {health.status_code}")
        failures += not ok
        if not ok:
            return _summary(failures)

        listed = client.get("/commands")
        body = listed.json()
        entries = body.get("commands", [])
        names = {item.get("name") for item in entries if isinstance(item, dict)}
        ok = listed.status_code == 200 and NAMES <= names
        record("PASS" if ok else "FAIL", "GET /commands", f"names={sorted(names)}")
        failures += not ok

        by_name = {item.get("name"): item for item in entries if isinstance(item, dict)}
        execute = by_name.get("amp_execute") or {}
        args = {item.get("name"): item for item in execute.get("args", []) if isinstance(item, dict)}
        prompt = args.get("prompt") or {}
        stream = args.get("stream_json") or {}
        ok = prompt.get("required") is True and stream.get("type") == "boolean" and stream.get("required") is False
        record(
            "PASS" if ok else "FAIL",
            "amp_execute signature",
            f"prompt={prompt} stream_json={stream}",
        )
        failures += not ok

        missing = client.post("/commands/amp_execute", json={})
        ok = 400 <= missing.status_code < 500
        record(
            "PASS" if ok else "FAIL",
            "POST /commands/amp_execute (no prompt)",
            f"HTTP {missing.status_code}",
        )
        failures += not ok

        failures += _version(client)
        failures += _setup(client)
        failures += _auth_or_live(client)
    return _summary(failures)


def _version(client: httpx.Client) -> int:
    response = client.post("/commands/amp_version", json={})
    try:
        payload = response.json()
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "POST /commands/amp_version", f"not JSON: {exc}")
        return 1
    if response.status_code == 200 and payload.get("result") == PINNED_VERSION:
        record("PASS", "POST /commands/amp_version", PINNED_VERSION)
        return 0
    error = payload.get("error", payload) if isinstance(payload, dict) else payload
    text = error if isinstance(error, str) else json.dumps(error, ensure_ascii=False)
    if response.status_code == 500 and "not found on PATH" in text:
        record("PASS", "POST /commands/amp_version", "amp is not on PATH; the error names the missing CLI")
        return 0
    record("FAIL", "POST /commands/amp_version", f"HTTP {response.status_code} {_short(payload)}")
    return 1


def _setup(client: httpx.Client) -> int:
    response = client.post("/commands/amp_setup_check", json={})
    try:
        payload = response.json()
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "POST /commands/amp_setup_check", f"not JSON: {exc}")
        return 1
    result = payload.get("result") if isinstance(payload, dict) else None
    if response.status_code != 200 or not isinstance(result, dict):
        record("FAIL", "POST /commands/amp_setup_check", f"HTTP {response.status_code} {_short(payload)}")
        return 1
    key_set = result.get("api_key_set")
    ok = (
        result.get("package") == "@ampcode/cli"
        and isinstance(key_set, bool)
        and isinstance(result.get("dangerously_allow_all"), bool)
        and isinstance(result.get("settings_exists"), bool)
        and isinstance(result.get("updates_mode"), str)
        and isinstance(result.get("settings_path"), str)
        and result["settings_path"]
        and isinstance(result.get("installed"), bool)
    )
    if result.get("installed"):
        ok = ok and result.get("version") == PINNED_VERSION
    else:
        ok = ok and result.get("version") == ""
    record(
        "PASS" if ok else "FAIL",
        "POST /commands/amp_setup_check",
        f"installed={result.get('installed')} version={result.get('version')} api_key_set={key_set}",
    )
    if not ok:
        return 1
    # Paths returned by a remote server belong to that server, not this client.
    repeated = client.post("/commands/amp_setup_check", json={})
    stable = repeated.status_code == 200 and repeated.json().get("result") == result
    record("PASS" if stable else "FAIL", "setup is stable across repeated inspection")
    return 0 if stable else 1


def _auth_or_live(client: httpx.Client) -> int:
    test = "POST /commands/amp_execute"
    forced_off = RUN_LLM in {"0", "false", "no"}
    if REQUIRE and forced_off:
        record("FAIL", test, "E2E_REQUIRE_LLM=1 conflicts with E2E_RUN_LLM=0")
        return 1
    if forced_off:
        record("SKIP", test, "E2E_RUN_LLM disables all execute calls")
        return 0
    # The server owns the credentials. The controller never needs a copy.
    setup = client.post("/commands/amp_setup_check", json={})
    result = setup.json().get("result", {})
    if setup.status_code != 200 or not isinstance(result.get("api_key_set"), bool):
        record("FAIL", test, "could not inspect remote Amp key presence")
        return 1
    if not result["api_key_set"]:
        response = client.post(
            "/commands/amp_execute",
            json={"prompt": f"Reply with exactly: {MARKER}"},
            timeout=20.0,
        )
        try:
            payload = response.json()
        except Exception as exc:  # noqa: BLE001
            record("FAIL", test, f"not JSON: {exc}")
            return 1
        error = ""
        if isinstance(payload, dict):
            error = str(payload.get("error") or "")
        ok = (
            response.status_code == 500
            and "AMP_API_KEY" in error
            and "device-login" in error
            and "user_code" not in error
            and "ampcode.com/auth" not in error
        )
        record(
            "PASS" if ok else "FAIL",
            "POST /commands/amp_execute (no AMP_API_KEY)",
            f"HTTP {response.status_code} {_short(error)}",
        )
        if REQUIRE:
            record("FAIL", test, "AMP_API_KEY is missing and E2E_REQUIRE_LLM=1")
            return 1
        return 0 if ok else 1
    return _coding(client)


def _coding(client: httpx.Client) -> int:
    """Prove code changes through remote files and isolated target processes."""
    failures = 0

    def check(ok: bool, label: str) -> None:
        nonlocal failures
        failures += not ok
        record("PASS" if ok else "FAIL", label)

    workspace = os.environ.get("E2E_WORKSPACE") or os.environ.get("E2E_BASE_DIR") or "/home/user/app"
    project = workspace.rstrip("/") + "/abx_e2e_amp_" + uuid.uuid4().hex
    marker = MARKER + "_" + uuid.uuid4().hex
    source = "def add(a, b):\n    return a - b\n"
    tests = ("import unittest\nfrom calculator import add\nclass AddTests(unittest.TestCase):\n"
             "    def test_positive(self): self.assertEqual(add(2, 3), 5)\n"
             "    def test_negative(self): self.assertEqual(add(-4, -3), -7)\n"
             "    def test_zero(self): self.assertEqual(add(0, 0), 0)\n")
    test_command = "env -i PATH=/usr/local/bin:/usr/bin:/bin python3 -I -c " + shlex.quote(
        "import sys,unittest;sys.path.insert(0,'.');"
        "result=unittest.TextTestRunner().run(unittest.defaultTestLoader.discover('.',pattern='test_calculator.py'));"
        "sys.exit(not result.wasSuccessful())"
    )

    def read(name: str) -> str:
        response = client.get("/files/download-stream", params={"path": project + "/" + name})
        response.raise_for_status()
        return base64.b64decode(response.json()["content_base64"]).decode()

    try:
        for name, content in (("calculator.py", source), ("test_calculator.py", tests)):
            response = client.post("/files/upload-stream", json={
                "path": project + "/" + name,
                "content_base64": base64.b64encode(content.encode()).decode(),
            })
            response.raise_for_status()
        response = client.post("/shell", json={"command": test_command, "cwd": project, "timeout": 30})
        before = response.json()
        reproduced = (response.status_code == 200 and before.get("exit_code") == 1
                      and "AssertionError" in before.get("stderr", "")
                      and "Ran 3 tests" in before.get("stderr", ""))
        check(reproduced, "L3 seeded source fails independent target tests")
        if not reproduced:
            return failures
        prompt = (f"Work exclusively in {project}. Fix calculator.py so add(a,b) adds numbers correctly. "
                  "Do not modify test_calculator.py. Create REPORT.md explaining the bug and fix. "
                  f"Create acceptance.txt containing exactly {marker} followed by a newline. "
                  "Perform these file edits and run the tests before finishing.")
        response = client.post("/commands/amp_execute", json={
            "prompt": prompt, "stream_json": False, "dangerously_allow_all": True,
        }, timeout=LLM_TIMEOUT)
        completed = response.status_code == 200 and isinstance(response.json().get("result"), str)
        check(completed, "L3 real headless coding request completes")
        if not completed:
            return failures
        check(read("calculator.py") != source, "L3 existing source changed on target")
        check(read("test_calculator.py") == tests, "L3 original independent tests preserved")
        check(bool(read("REPORT.md").strip()), "L3 new report artifact downloaded")
        check(read("acceptance.txt") == marker + "\n", "L3 new exact artifact downloaded")
        response = client.post("/shell", json={"command": test_command, "cwd": project, "timeout": 30})
        after = response.json()
        check(response.status_code == 200 and after.get("exit_code") == 0
              and "Ran 3 tests" in after.get("stderr", ""), "L3 independent target tests pass")
        heldout = (
            "import importlib.util;"
            f"spec=importlib.util.spec_from_file_location('calculator_under_test',{project + '/calculator.py'!r});"
            "module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);"
            "assert all(module.add(a,b)==a+b for a,b in [(2,3),(-4,-3),(0,0),(127,83),(-91,13),(0.5,1.25)]);"
            "print('INDEPENDENT_OK')"
        )
        response = client.post("/shell", json={
            "command": "env -i PATH=/usr/local/bin:/usr/bin:/bin python3 -I -c " + shlex.quote(heldout),
            "cwd": project, "timeout": 30,
        })
        checked = response.json()
        check(response.status_code == 200 and checked.get("exit_code") == 0
              and checked.get("stdout", "").strip() == "INDEPENDENT_OK", "L3 held-out target assertions pass")
    except Exception as exc:
        check(False, f"L3 aborted ({type(exc).__name__}); response omitted")
    finally:
        response = client.delete("/files", params={"path": project})
        check(response.status_code in {200, 404}, "L3 owned project cleanup")
    return failures


def _summary(failures: int) -> int:
    failed = sum(1 for status, _, _ in RESULTS if status == "FAIL")
    passed = sum(1 for status, _, _ in RESULTS if status == "PASS")
    skipped = sum(1 for status, _, _ in RESULTS if status == "SKIP")
    print(f"{passed} passed, {failed} failed, {skipped} skipped", flush=True)
    return 1 if failed or failures else 0


if __name__ == "__main__":
    sys.exit(main())
