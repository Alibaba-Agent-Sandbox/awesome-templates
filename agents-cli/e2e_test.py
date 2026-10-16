#!/usr/bin/env python3
"""Actual pinned-CLI diagnostics and restricted HTTP contracts, without model turns.

Fixture adapters are exercised only by test_protocol.py using an explicit test PATH.
This smoke never infers real coding acceptance from a protocol message.
"""
from __future__ import annotations

import os
import sys

import httpx

EXPECTED = "codex 0.162.1; qwen-code 0.23.0"


def check(ok: bool, label: str) -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {label}", flush=True)
    if not ok:
        raise AssertionError(label)


def main() -> int:
    headers = {}
    gateway_token = os.environ.get("E2E_TOKEN", "")
    server_token = os.environ.get("E2E_SERVER_TOKEN") or os.environ.get("ABX_SERVER_TOKEN", "")
    if gateway_token:
        headers["X-Access-Token"] = gateway_token
    if server_token:
        headers["Authorization"] = "Bearer " + server_token
    workspace = os.environ.get("E2E_WORKSPACE") or os.environ.get("WORKSPACE") or "/home/user/workspace"
    with httpx.Client(base_url=os.environ.get("E2E_BASE_URL", "http://127.0.0.1:9000"),
                      headers=headers, timeout=60) as client:
        response = client.get("/health")
        check(response.status_code == 200 and response.json().get("status") == "ok", "health")
        response = client.get("/commands")
        check(response.status_code == 200 and
              {item["name"] for item in response.json().get("commands", [])} == {"agents_version"},
              "named diagnostics only")
        response = client.post("/commands/agents_version", json={})
        check(response.status_code == 200 and response.json().get("result") == EXPECTED,
              "both actual installed CLI versions match pins")
        response = client.get("/v1/agents/runtimes")
        entries = {item["id"]: item for item in response.json().get("data", [])}
        check(response.status_code == 200 and all(
            entries.get(name, {}).get("implemented") is True and entries[name].get("installed") is True
            for name in ("codex", "qwen-code")), "both local runtimes are implemented and installed")
        for method, path in (("POST", "/shell"), ("GET", "/files"),
                             ("POST", "/process/start"), ("GET", "/v1/models"),
                             ("POST", "/v1/agents/responses")):
            response = client.request(method, path, json={} if method == "POST" else None)
            check(response.status_code == 404, "disabled route remains inaccessible: " + path)
        response = client.post("/v1/agents/sessions", json={"adapter": "claude-code"})
        check(response.status_code == 404, "unimplemented runtime is rejected")
        sessions = []
        for adapter in ("codex", "qwen-code"):
            response = client.post("/v1/agents/sessions", json={
                "adapter": adapter, "agent": {"model": adapter},
                "environment": {"type": "self_hosted", "workspace_directory": workspace},
            })
            check(response.status_code == 200 and response.headers.get("X-Agent-Sandbox-Local") == "1"
                  and isinstance(response.json().get("id"), str), adapter + " session creates without a turn")
            session = response.json()["id"]
            sessions.append(session)
            response = client.get("/v1/agents/sessions/" + session)
            check(response.status_code == 200 and response.json().get("id") == session,
                  adapter + " session reconnects")
            response = client.get("/v1/agents/sessions/" + session + "/items")
            check(response.status_code == 200 and response.json().get("data") == [],
                  adapter + " new session has no model output")
        response = client.get("/v1/agents/sessions")
        check(response.status_code == 200 and set(sessions) <= {item["id"] for item in response.json().get("data", [])},
              "created sessions are listed")
        if server_token:
            response = httpx.get(str(client.base_url).rstrip("/") + "/commands", timeout=10)
            check(response.status_code == 401, "server token protects business routes")
    requested = any(os.environ.get(name, "").lower() in {"1", "true", "yes"}
                    for name in ("E2E_RUN_LLM", "E2E_REQUIRE_LLM"))
    check(not requested, "no L3 pass without an out-of-band artifact verifier")
    print("[SKIP] model/coding acceptance: no model turn or artifact acceptance was performed", flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"[FAIL] HTTP smoke aborted ({type(exc).__name__}); response omitted", flush=True)
        sys.exit(1)
