#!/usr/bin/env python3
"""Local smoke for the amp template against E2E_BASE_URL.

Express runs go through scripts/express_e2e.py (CLI and SDK). This file is
the no-cloud check. A live ``amp -x`` call is SKIP unless AMP_API_KEY is set
and E2E_RUN_LLM is not 0. E2E_REQUIRE_LLM=1 turns a missing key or a missing
ABX_E2E_OK marker into FAIL.
"""
from __future__ import annotations

import json
import os
import sys

import httpx

BASE_URL = os.environ.get("E2E_BASE_URL", "http://127.0.0.1:9000").rstrip("/")
PINNED_VERSION = "0.0.1792022479-ge66e24"
MARKER = "ABX_E2E_OK"
TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=10.0)
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
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
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
        and result.get("dangerously_allow_all") is True
        and result.get("updates_mode") == "disabled"
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
    path = result["settings_path"]
    try:
        settings = json.loads(open(path, encoding="utf-8").read())
    except OSError as exc:
        record("FAIL", "settings file", f"unreadable {path}: {exc}")
        return 1
    file_ok = (
        settings.get("amp.dangerouslyAllowAll") is True
        and settings.get("amp.updates.mode") == "disabled"
        and settings.get("amp.notifications.enabled") is False
    )
    record("PASS" if file_ok else "FAIL", "settings file", path)
    return 0 if file_ok else 1


def _auth_or_live(client: httpx.Client) -> int:
    test = "POST /commands/amp_execute"
    key = os.environ.get("AMP_API_KEY", "").strip()
    forced_off = RUN_LLM in {"0", "false", "no"}
    if REQUIRE and forced_off:
        record("FAIL", test, "E2E_REQUIRE_LLM=1 conflicts with E2E_RUN_LLM=0")
        return 1
    if not key:
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
    if forced_off:
        record("SKIP", test, f"E2E_RUN_LLM={RUN_LLM!r}; AMP_API_KEY is set but the live call is off")
        return 0
    try:
        response = client.post(
            "/commands/amp_execute",
            json={"prompt": f"Reply with exactly: {MARKER}", "stream_json": False},
            timeout=LLM_TIMEOUT,
        )
        payload = response.json()
    except Exception as exc:  # noqa: BLE001
        record("FAIL", test, f"exception: {exc}")
        return 1
    result = payload.get("result") if isinstance(payload, dict) else None
    found = isinstance(result, str) and MARKER in result
    ok = response.status_code == 200 and found
    detail = f"HTTP {response.status_code}, marker={found}"
    if not ok and isinstance(payload, dict):
        detail += f", error={_short(payload.get('error') or payload)}"
    record("PASS" if ok else "FAIL", test, detail)
    return 0 if ok else 1


def _summary(failures: int) -> int:
    failed = sum(1 for status, _, _ in RESULTS if status == "FAIL")
    passed = sum(1 for status, _, _ in RESULTS if status == "PASS")
    skipped = sum(1 for status, _, _ in RESULTS if status == "SKIP")
    print(f"{passed} passed, {failed} failed, {skipped} skipped", flush=True)
    return 1 if failed or failures else 0


if __name__ == "__main__":
    sys.exit(main())
