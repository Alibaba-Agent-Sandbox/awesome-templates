#!/usr/bin/env python3
"""Local smoke for the opencode template against E2E_BASE_URL.

Express runs go through scripts/express_e2e.py, which uses ``abx run`` and
``from agent_sandbox import Sandbox``. This file is the no-cloud check.
When ``E2E_SANDBOX_ID`` is set, the same assertions also run through
``Sandbox.connect``.
"""
from __future__ import annotations

import json
import os
import shutil
import sys

import httpx

BASE_URL = os.environ.get("E2E_BASE_URL", "http://127.0.0.1:9000").rstrip("/")
SANDBOX_ID = os.environ.get("E2E_SANDBOX_ID", "").strip()
TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=10.0)
LLM_TIMEOUT = float(os.environ.get("E2E_LLM_TIMEOUT", "180"))
RUN_LLM = os.environ.get("E2E_RUN_LLM", "").strip().lower()
REQUIRE = os.environ.get("E2E_REQUIRE_LLM", "").strip().lower() in {"1", "true", "yes"}
API_KEY = os.environ.get("ABX_LLM_API_KEY", "").strip()
MARKER = "ABX_E2E_OK"
PINNED = "1.19.0"
REQUIRED = {
    "opencode",
    "opencode_run",
    "opencode_serve_start",
    "opencode_serve_status",
    "opencode_serve_stop",
    "opencode_version",
    "opencode_setup_check",
}
RUN_PARAMS = {"prompt", "model", "agent", "session", "continue_session", "cwd"}

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


def check_health(client: httpx.Client) -> None:
    response = client.get("/health")
    body = response.json()
    ok = response.status_code == 200 and body.get("status") == "ok"
    record("PASS" if ok else "FAIL", "GET /health", f"HTTP {response.status_code}")


def check_commands(client: httpx.Client) -> None:
    response = client.get("/commands")
    body = response.json()
    entries = body.get("commands", [])
    names = {item.get("name") for item in entries if isinstance(item, dict)}
    missing = sorted(REQUIRED - names)
    run = next((item for item in entries if item.get("name") == "opencode_run"), None)
    params = {arg.get("name") for arg in (run or {}).get("args", [])}
    param_gap = sorted(RUN_PARAMS - params)
    ok = response.status_code == 200 and not missing and not param_gap
    detail = f"missing={missing or '-'} params={param_gap or '-'}"
    record("PASS" if ok else "FAIL", "GET /commands", detail)


def check_missing_prompt(client: httpx.Client) -> None:
    response = client.post("/commands/opencode_run", json={})
    ok = response.status_code == 400
    record(
        "PASS" if ok else "FAIL",
        "POST /commands/opencode_run without prompt",
        f"HTTP {response.status_code}",
    )


def check_version_and_setup(client: httpx.Client) -> None:
    if shutil.which("opencode") is None:
        record("SKIP", "opencode_version", "opencode is not on PATH")
        record("SKIP", "opencode_setup_check", "opencode is not on PATH")
        return
    version = client.post("/commands/opencode_version", json={})
    body = version.json()
    ok = version.status_code == 200 and body.get("result") == PINNED
    record("PASS" if ok else "FAIL", "opencode_version", _short(body))
    setup = client.post("/commands/opencode_setup_check", json={})
    body = setup.json()
    ok = setup.status_code == 200 and body.get("result") == "ok"
    record("PASS" if ok else "FAIL", "opencode_setup_check", _short(body))


def check_serve(client: httpx.Client) -> None:
    if shutil.which("opencode") is None:
        record("SKIP", "opencode_serve_start", "opencode is not on PATH")
        return
    port = 18096
    try:
        started = client.post(
            "/commands/opencode_serve_start",
            json={"port": port, "hostname": "127.0.0.1"},
            timeout=30.0,
        )
        body = started.json()
        result = body.get("result") if isinstance(body, dict) else None
        ok = (
            started.status_code == 200
            and isinstance(result, dict)
            and result.get("healthy") is True
            and result.get("port") == port
        )
        record("PASS" if ok else "FAIL", "opencode_serve_start", _short(body))
        if ok:
            health = httpx.get(f"http://127.0.0.1:{port}/global/health", timeout=5.0)
            payload = health.json()
            healthy = health.status_code == 200 and payload.get("healthy") is True
            record(
                "PASS" if healthy else "FAIL",
                "GET /global/health",
                _short(payload),
            )
        status = client.post("/commands/opencode_serve_status", json={})
        state = status.json().get("result")
        running = isinstance(state, dict) and state.get("running") is True
        record("PASS" if running else "FAIL", "opencode_serve_status", _short(status.json()))
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "opencode_serve_start", str(exc))
    finally:
        try:
            stopped = client.post("/commands/opencode_serve_stop", json={})
            ok = stopped.status_code == 200 and stopped.json().get("result") == "stopped"
            record("PASS" if ok else "FAIL", "opencode_serve_stop", _short(stopped.text))
        except Exception as exc:  # noqa: BLE001
            record("FAIL", "opencode_serve_stop", str(exc))


def _marker_in(result: object) -> bool:
    if isinstance(result, str):
        return MARKER in result
    if isinstance(result, dict):
        return MARKER in json.dumps(result)
    return False


def check_model_call(client: httpx.Client) -> None:
    test = "POST /commands/opencode_run"
    forced_off = RUN_LLM in {"0", "false", "no"}
    if REQUIRE and forced_off:
        record("FAIL", test, "E2E_REQUIRE_LLM=1 conflicts with E2E_RUN_LLM=0")
        return
    if forced_off:
        record("SKIP", test, f"E2E_RUN_LLM={RUN_LLM!r}")
        return
    if not API_KEY:
        status = "FAIL" if REQUIRE or RUN_LLM in {"1", "true", "yes"} else "SKIP"
        record(status, test, "ABX_LLM_API_KEY is missing")
        return
    if shutil.which("opencode") is None:
        record("FAIL" if REQUIRE else "SKIP", test, "opencode is not on PATH")
        return
    response = client.post(
        "/commands/opencode_run",
        json={"prompt": f"Reply with exactly the token {MARKER} and nothing else."},
        timeout=LLM_TIMEOUT,
    )
    body = response.json()
    found = response.status_code == 200 and _marker_in(body.get("result"))
    detail = f"HTTP {response.status_code}, marker={found}"
    if not found:
        detail += f", body={_short(body)}"
    record("PASS" if found else "FAIL", test, detail)


def check_sdk() -> None:
    if not SANDBOX_ID:
        record("SKIP", "Sandbox.connect", "E2E_SANDBOX_ID is unset")
        return
    import asyncio

    from agent_sandbox import Sandbox

    async def _call() -> None:
        sandbox = await Sandbox.connect(SANDBOX_ID)
        try:
            version = await sandbox.run("opencode_version")
            setup = await sandbox.run("opencode_setup_check")
            ok = version == PINNED and setup == "ok"
            record("PASS" if ok else "FAIL", "Sandbox.run", f"version={version!r} setup={setup!r}")
        finally:
            close = getattr(sandbox, "close", None)
            if callable(close):
                await close()

    asyncio.run(_call())


def main() -> int:
    print(f"opencode e2e  base_url={BASE_URL}", flush=True)
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
        check_health(client)
        check_commands(client)
        check_missing_prompt(client)
        check_version_and_setup(client)
        check_serve(client)
        check_model_call(client)
    check_sdk()
    failed = sum(1 for status, _, _ in RESULTS if status == "FAIL")
    passed = sum(1 for status, _, _ in RESULTS if status == "PASS")
    skipped = sum(1 for status, _, _ in RESULTS if status == "SKIP")
    print(f"SUMMARY {passed} PASS, {skipped} SKIP, {failed} FAIL", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
