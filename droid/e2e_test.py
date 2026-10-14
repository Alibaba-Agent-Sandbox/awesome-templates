#!/usr/bin/env python3
"""End-to-end checks for the ``droid`` template.

Uses httpx against a running sandbox server:

- ``GET /health``
- ``GET /commands`` lists ``droid``
- ``POST /commands/droid`` without ``prompt`` is a client error
- the LLM call is SKIP when ``FACTORY_API_KEY`` is unset, or when
  ``E2E_RUN_LLM=0``

Usage::

    python3 e2e_test.py
    E2E_BASE_URL=http://host:9000 python3 e2e_test.py
    E2E_RUN_LLM=0 python3 e2e_test.py
    FACTORY_API_KEY=fk-... python3 e2e_test.py
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any

import httpx

TEMPLATE = "droid"
CMD = "droid"
BASE_URL = os.environ.get("E2E_BASE_URL", "http://localhost:9000").rstrip("/")
TOKEN = os.environ.get("E2E_TOKEN", "")
TIMEOUT = httpx.Timeout(
    connect=10.0,
    read=float(os.environ.get("E2E_TIMEOUT", "60")),
    write=30.0,
    pool=10.0,
)
LLM_TIMEOUT = float(os.environ.get("E2E_LLM_TIMEOUT", "420"))
RUN_LLM = os.environ.get("E2E_RUN_LLM", "").strip().lower()
REQUIRE = os.environ.get("E2E_REQUIRE_LLM", "").strip().lower() in {"1", "true", "yes"}
KEY_ENV = "FACTORY_API_KEY"
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


def preflight(client: httpx.Client) -> bool:
    try:
        resp = client.get("/health")
        body = resp.json()
        ok = resp.status_code == 200 and body.get("status") == "ok"
        record("PASS" if ok else "FAIL", "GET /health", f"HTTP {resp.status_code}, status={body.get('status')}")
        return ok
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "GET /health", f"exception: {exc}")
        return False


def check_commands(client: httpx.Client) -> None:
    try:
        resp = client.get("/commands")
        body = resp.json()
        entries = body.get("commands", body if isinstance(body, list) else [])
        by_name = {c.get("name"): c for c in entries if isinstance(c, dict)}
        entry = by_name.get(CMD) or {}
        args = {
            a.get("name"): a
            for a in entry.get("args", [])
            if isinstance(a, dict)
        }
        prompt = args.get("prompt") or {}
        ok = (
            resp.status_code == 200
            and entry != {}
            and prompt.get("type") == "string"
            and prompt.get("required") is True
        )
        record(
            "PASS" if ok else "FAIL",
            "GET /commands",
            f"HTTP {resp.status_code}, names={sorted(by_name)}, "
            f"prompt type={prompt.get('type')} required={prompt.get('required')}",
        )
    except Exception as exc:  # noqa: BLE001
        record("FAIL", "GET /commands", f"exception: {exc}")


def check_missing_prompt(client: httpx.Client) -> None:
    try:
        resp = client.post(f"/commands/{CMD}", json={})
        body = resp.json()
        client_error = 400 <= resp.status_code < 500
        mentions = "prompt" in str(body.get("error", "")).lower() or "Required argument" in str(
            body.get("error", "")
        )
        ok = client_error and mentions
        record(
            "PASS" if ok else "FAIL",
            f"POST /commands/{CMD} (no prompt)",
            f"HTTP {resp.status_code} (expected client error), error={_short(body.get('error'), 120)}",
        )
    except Exception as exc:  # noqa: BLE001
        record("FAIL", f"POST /commands/{CMD} (no prompt)", f"exception: {exc}")


def check_llm(client: httpx.Client) -> None:
    test = f"POST /commands/{CMD}"
    forced_off = RUN_LLM in {"0", "false", "no"}
    has_key = bool(os.environ.get(KEY_ENV, "").strip())
    if REQUIRE and forced_off:
        record("FAIL", test, "E2E_REQUIRE_LLM=1 conflicts with E2E_RUN_LLM=0")
        return
    if forced_off:
        record("SKIP", test, f"E2E_RUN_LLM={RUN_LLM!r} — forced skip")
        return
    if not has_key:
        status = "FAIL" if REQUIRE or RUN_LLM in {"1", "true", "yes"} else "SKIP"
        record(status, test, f"{KEY_ENV} is missing")
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
            detail += f", error={_short(body.get('error') or body, 140)}"
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
    print(f"  llm case : {'forced' if RUN_LLM in {'1', 'true', 'yes'} else 'auto'}", flush=True)
    print("-" * 74, flush=True)
    with _client() as client:
        if not preflight(client):
            print("server unreachable — aborting", flush=True)
            return 2
        check_commands(client)
        check_missing_prompt(client)
        check_llm(client)
    return summary()


if __name__ == "__main__":
    sys.exit(main())
