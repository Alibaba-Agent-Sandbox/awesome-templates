#!/usr/bin/env python3
"""End-to-end checks for the ``amp`` template. Only ``httpx`` is required.

Checks:

- ``GET /health`` returns 200 with ``{"status": "ok"}``.
- ``GET /commands`` includes the registered ``amp`` command.
- ``POST /commands/amp`` without ``prompt`` is a client error (HTTP 4xx).
- The LLM call is ``SKIP`` when ``E2E_RUN_LLM=0`` or ``AMP_API_KEY`` is missing.

The process exits 0 unless a check records ``FAIL``. ``SKIP`` is not a failure.

Usage::

    python3 e2e_test.py
    E2E_BASE_URL=http://127.0.0.1:9000 python3 e2e_test.py
    E2E_RUN_LLM=0 python3 e2e_test.py
    AMP_API_KEY=... python3 e2e_test.py
"""
from __future__ import annotations

import json
import os
import sys

import httpx

TEMPLATE = "amp"
CMD = "amp"
BASE_URL = os.environ.get("E2E_BASE_URL", "http://127.0.0.1:9000").rstrip("/")
TOKEN = os.environ.get("E2E_TOKEN", "")
TIMEOUT = httpx.Timeout(
    connect=10.0,
    read=float(os.environ.get("E2E_TIMEOUT", "60")),
    write=30.0,
    pool=10.0,
)
LLM_TIMEOUT = float(os.environ.get("E2E_LLM_TIMEOUT", "600"))
RUN_LLM = os.environ.get("E2E_RUN_LLM", "").strip().lower()
REQUIRE = os.environ.get("E2E_REQUIRE_LLM", "").strip().lower() in {"1", "true", "yes"}
MARKER = "ABX_E2E_OK"
LLM_PROMPT = f"Reply with exactly: {MARKER}"

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


def check_health(client: httpx.Client) -> bool:
    test = "GET /health"
    try:
        resp = client.get("/health")
        body = resp.json()
        ok = resp.status_code == 200 and body.get("status") == "ok"
        record("PASS" if ok else "FAIL", test, f"HTTP {resp.status_code}, status={body.get('status')}")
        return ok
    except Exception as exc:  # noqa: BLE001
        record("FAIL", test, f"exception: {exc}")
        return False


def check_commands(client: httpx.Client) -> None:
    test = "GET /commands"
    try:
        resp = client.get("/commands")
        body = resp.json()
        entries = body.get("commands", body if isinstance(body, list) else [])
        names = [c.get("name") for c in entries if isinstance(c, dict)]
        ok = resp.status_code == 200 and CMD in names
        record(
            "PASS" if ok else "FAIL",
            test,
            f"HTTP {resp.status_code}, includes {CMD}={CMD in names}, names={names}",
        )
    except Exception as exc:  # noqa: BLE001
        record("FAIL", test, f"exception: {exc}")


def check_missing_prompt(client: httpx.Client) -> None:
    test = f"POST /commands/{CMD} (no prompt)"
    try:
        resp = client.post(f"/commands/{CMD}", json={})
        try:
            body = resp.json()
        except Exception:  # noqa: BLE001
            body = {"_raw": resp.text}
        ok = 400 <= resp.status_code < 500
        record(
            "PASS" if ok else "FAIL",
            test,
            f"HTTP {resp.status_code} client error={ok}, error={_short(body.get('error', body) if isinstance(body, dict) else body)}",
        )
    except Exception as exc:  # noqa: BLE001
        record("FAIL", test, f"exception: {exc}")


def check_llm(client: httpx.Client) -> None:
    test = f"POST /commands/{CMD}"
    key = os.environ.get("AMP_API_KEY", "").strip()
    forced_off = RUN_LLM in {"0", "false", "no"}
    if REQUIRE and forced_off:
        record("FAIL", test, "E2E_REQUIRE_LLM=1 conflicts with E2E_RUN_LLM=0")
        return
    if forced_off:
        record("SKIP", test, f"E2E_RUN_LLM={RUN_LLM!r}")
        return
    if not key:
        status = "FAIL" if REQUIRE or RUN_LLM in {"1", "true", "yes"} else "SKIP"
        record(status, test, "AMP_API_KEY is missing")
        return

    try:
        resp = client.post(
            f"/commands/{CMD}",
            json={"prompt": LLM_PROMPT},
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
        record("FAIL", test, f"exception: {exc}")


def summary() -> int:
    passed = sum(1 for status, _, _ in RESULTS if status == "PASS")
    failed = sum(1 for status, _, _ in RESULTS if status == "FAIL")
    skipped = sum(1 for status, _, _ in RESULTS if status == "SKIP")
    print("\n" + "=" * 74, flush=True)
    print(f"SUMMARY — {TEMPLATE}", flush=True)
    print("=" * 74, flush=True)
    print(f"{passed} passed, {failed} failed, {skipped} skipped (total {len(RESULTS)})", flush=True)
    if failed:
        print("\nFailed tests:", flush=True)
        for status, name, detail in RESULTS:
            if status == "FAIL":
                print(f"  - {name}: {detail}", flush=True)
    print("=" * 74, flush=True)
    return 1 if failed else 0


def main() -> int:
    print(f"{TEMPLATE} end-to-end suite", flush=True)
    print(f"  base_url : {BASE_URL}", flush=True)
    print("-" * 74, flush=True)
    with _client() as client:
        if not check_health(client):
            return summary()
        check_commands(client)
        check_missing_prompt(client)
        check_llm(client)
    return summary()


if __name__ == "__main__":
    sys.exit(main())
