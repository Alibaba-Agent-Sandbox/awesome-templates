#!/usr/bin/env python3
"""HTTP checks for the opencode template. Only httpx is required.

The server must already be running (``python3 commands.py``).

Checks:

- ``GET /health``
- ``GET /commands`` lists ``opencode``
- ``POST /commands/opencode`` without ``prompt`` is a client error
- the real model call is SKIP when ``E2E_RUN_LLM`` is ``0`` or
  ``OPENCODE_API_KEY`` is missing

Exit 0 when no line is FAIL.
"""
from __future__ import annotations

import json
import os
import sys

import httpx

BASE_URL = os.environ.get("E2E_BASE_URL", "http://127.0.0.1:9000").rstrip("/")
TOKEN = os.environ.get("E2E_TOKEN", "")
TIMEOUT = httpx.Timeout(
    connect=10.0,
    read=float(os.environ.get("E2E_TIMEOUT", "60")),
    write=30.0,
    pool=10.0,
)
LLM_TIMEOUT = float(os.environ.get("E2E_LLM_TIMEOUT", "620"))
RUN_LLM = os.environ.get("E2E_RUN_LLM", "").strip().lower()
REQUIRE = os.environ.get("E2E_REQUIRE_LLM", "").strip().lower() in {"1", "true", "yes"}
API_KEY = os.environ.get("OPENCODE_API_KEY", "").strip()
MARKER = "ABX_E2E_OK"

RESULTS: list[tuple[str, str, str]] = []


def record(status: str, test: str, detail: str = "") -> None:
    RESULTS.append((status, test, detail))
    line = f"[{status}] {test}"
    if detail:
        line += f" — {detail}"
    print(line, flush=True)


def _short(value: object, limit: int = 160) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _client() -> httpx.Client:
    headers = {"X-Access-Token": TOKEN} if TOKEN else {}
    return httpx.Client(base_url=BASE_URL, timeout=TIMEOUT, headers=headers)


def check_health(client: httpx.Client) -> None:
    try:
        resp = client.get("/health")
        body = resp.json()
        ok = resp.status_code == 200 and body.get("status") == "ok"
        record("PASS" if ok else "FAIL", "GET /health", f"HTTP {resp.status_code}")
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "GET /health", str(exc))


def check_commands(client: httpx.Client) -> None:
    try:
        resp = client.get("/commands")
        body = resp.json()
        entries = body.get("commands", body if isinstance(body, list) else [])
        names = [
            item.get("name")
            for item in entries
            if isinstance(item, dict)
        ]
        ok = resp.status_code == 200 and "opencode" in names
        record(
            "PASS" if ok else "FAIL",
            "GET /commands",
            f"HTTP {resp.status_code}, names={names}",
        )
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "GET /commands", str(exc))


def check_missing_prompt(client: httpx.Client) -> None:
    try:
        resp = client.post("/commands/opencode", json={})
        ok = 400 <= resp.status_code < 500
        record(
            "PASS" if ok else "FAIL",
            "POST /commands/opencode without prompt",
            f"HTTP {resp.status_code} (expected client error), {_short(resp.text)}",
        )
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "POST /commands/opencode without prompt", str(exc))


def check_model_call(client: httpx.Client) -> None:
    test = "POST /commands/opencode"
    forced_off = RUN_LLM in {"0", "false", "no"}
    if REQUIRE and forced_off:
        record("FAIL", test, "E2E_REQUIRE_LLM=1 conflicts with E2E_RUN_LLM=0")
        return
    if forced_off:
        record("SKIP", test, f"E2E_RUN_LLM={RUN_LLM!r}")
        return
    if not API_KEY:
        status = "FAIL" if REQUIRE or RUN_LLM in {"1", "true", "yes"} else "SKIP"
        record(status, test, "OPENCODE_API_KEY is missing")
        return
    try:
        resp = client.post(
            "/commands/opencode",
            json={"prompt": f"Reply with exactly: {MARKER}"},
            timeout=LLM_TIMEOUT,
        )
        body = resp.json()
        result = body.get("result")
        found = isinstance(result, str) and MARKER in result
        ok = resp.status_code == 200 and found
        detail = f"HTTP {resp.status_code}, marker={found}"
        if not ok:
            detail += f", error={_short(body.get('error') or body)}"
        record("PASS" if ok else "FAIL", test, detail)
    except Exception as exc:  # noqa: BLE001
        record("FAIL", test, str(exc))


def main() -> int:
    print(f"opencode e2e  base_url={BASE_URL}", flush=True)
    with _client() as client:
        check_health(client)
        check_commands(client)
        check_missing_prompt(client)
        check_model_call(client)
    failed = sum(1 for status, _, _ in RESULTS if status == "FAIL")
    passed = sum(1 for status, _, _ in RESULTS if status == "PASS")
    skipped = sum(1 for status, _, _ in RESULTS if status == "SKIP")
    print(f"SUMMARY {passed} PASS, {skipped} SKIP, {failed} FAIL", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
