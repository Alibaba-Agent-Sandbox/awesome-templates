#!/usr/bin/env python3
"""Local smoke for _skeleton against E2E_BASE_URL.

Express runs go through scripts/express_e2e.py, which uses the CLI and
``from agent_sandbox import ProviderSandbox``. This file is the no-cloud check.
"""
from __future__ import annotations

import os
import sys

import httpx

BASE_URL = os.environ.get("E2E_BASE_URL", "http://127.0.0.1:9000").rstrip("/")
TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=10.0)


def main() -> int:
    failures = 0
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
        health = client.get("/health")
        ok = health.status_code == 200 and health.json().get("status") == "ok"
        print(f"[{'PASS' if ok else 'FAIL'}] GET /health", flush=True)
        failures += not ok

        listed = client.get("/commands")
        names = {item.get("name") for item in listed.json().get("commands", [])}
        ok = listed.status_code == 200 and names == {"hello"}
        print(f"[{'PASS' if ok else 'FAIL'}] GET /commands {sorted(names)}", flush=True)
        failures += not ok

        for label, body, expected in (
            ("default", {}, "Hello, World!"),
            ("named", {"name": "E2E"}, "Hello, E2E!"),
        ):
            response = client.post("/commands/hello", json=body)
            payload = response.json()
            ok = response.status_code == 200 and payload.get("result") == expected
            print(f"[{'PASS' if ok else 'FAIL'}] POST /commands/hello ({label})", flush=True)
            failures += not ok
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
