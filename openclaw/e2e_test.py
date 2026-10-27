#!/usr/bin/env python3
"""HTTP contract smoke; optional real authenticated gateway lifecycle.

OPENCLAW_GATEWAY_TOKEN must be injected into the running server as well as this
client. Gateway success is independent of any model/coding acceptance.
"""
import os
import sys

import httpx

# The host runner passes provider gateway authentication separately from app auth.
import json as _e2e_json
_GATEWAY_HEADERS = _e2e_json.loads(os.environ.get("E2E_GATEWAY_HEADERS_JSON", "{}"))
if not isinstance(_GATEWAY_HEADERS, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in _GATEWAY_HEADERS.items()):
    raise ValueError("E2E_GATEWAY_HEADERS_JSON must be an object of string headers")
_APPLICATION_HEADERS = {"Authorization": "Bearer " + os.environ["ABX_SERVER_TOKEN"]} if os.environ.get("ABX_SERVER_TOKEN") else {}

NAMES = { "gateway_start", "gateway_status", "gateway_stop", "gateway_health", "gateway_chat"}


def check(condition, label):
    print(f"[{'PASS' if condition else 'FAIL'}] {label}", flush=True)
    if not condition:
        raise AssertionError(label)


def main():
    headers = {}
    if os.environ.get("ABX_SERVER_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["ABX_SERVER_TOKEN"]
    with httpx.Client(base_url=os.environ.get("E2E_BASE_URL", "http://127.0.0.1:9000"),
                      headers={**(headers), **_GATEWAY_HEADERS, **_APPLICATION_HEADERS}, timeout=420) as client:
        response = client.get("/health")
        check(response.status_code == 200 and response.json().get("status") == "ok", "server health")
        response = client.get("/commands")
        check(response.status_code == 200 and NAMES <= {c['name'] for c in response.json()['commands']}, "registered lifecycle commands")
        check("gateway" not in {c['name'] for c in response.json()['commands']}, "retired command absent from discovery")
        response = client.post("/commands/gateway", json={})
        check(response.status_code == 404, "retired command invocation is 404")
        response = client.post("/commands/gateway_start", json={"port": "not-a-number"})
        check(response.status_code == 400 and response.json().get("type") == "TypeError", "invalid argument type is HTTP 400")
        response = client.post("/commands/gateway_status", json={})
        check(response.status_code == 200 and response.json()['result']['running'] is False, "initial owned status is stopped")
        if os.environ.get("OPENCLAW_GATEWAY_TOKEN"):
            try:
                response = client.post("/commands/gateway_start", json={"port": int(os.environ.get("E2E_GATEWAY_PORT", "18789")), "command_timeout": 90})
                check(response.status_code == 200 and response.json()['result'].get('healthy') is True, "real gateway authenticated readiness")
                response = client.post("/commands/gateway_health", json={"command_timeout": 20})
                check(response.status_code == 200 and response.json()['result'].get('healthy') is True, "real gateway authenticated health")
                response = client.post("/commands/gateway_status", json={})
                check(response.status_code == 200 and response.json()['result'].get('running') is True, "real gateway remains running after start response")
                if os.environ.get("E2E_REQUIRE_LLM") == "1":
                    prompt = 'Read these expenses: taxi 12.50, lunch 23.80, train 15.00. Reply only JSON with count (integer) and total (two-decimal string). No tools.'
                    response = client.post("/commands/gateway_chat", json={"prompt": prompt})
                    check(response.status_code == 200, "native gateway actual model turn")
                    result = response.json()['result']
                    parsed = __import__('json').loads(result['text'].strip().removeprefix('```json').removesuffix('```').strip())
                    check(parsed == {"count": 3, "total": "51.30"}, "independent expense count and decimal total")
                    response = client.post("/commands/gateway_chat", json={"prompt": 'Using the previous expenses, remove the train. Reply only JSON with count (integer) and total (two-decimal string). No tools.', "session_id": result['session_id']})
                    check(response.status_code == 200, "native gateway same-session follow-up")
                    follow = response.json()['result']
                    parsed = __import__('json').loads(follow['text'].strip().removeprefix('```json').removesuffix('```').strip())
                    check(follow['session_id'] == result['session_id'] and parsed == {"count": 2, "total": "36.30"}, "native conversation continuation retains earlier expense context")
            finally:
                response = client.post("/commands/gateway_stop", json={"command_timeout": 10})
                check(response.status_code == 200 and response.json()['result'].get('running') is False, "owned gateway cleanup")
            response = client.post("/commands/gateway_start", json={"command_timeout": 90})
            check(response.status_code == 200 and response.json()['result']['healthy'] is True, "immediate owned restart tolerates previous TCP TIME_WAIT")
            response = client.post("/commands/gateway_stop", json={})
            check(response.status_code == 200 and response.json()['result']['running'] is False, "restarted gateway independently stopped")
            response = client.post("/commands/gateway_health", json={"command_timeout": 1})
            check(response.status_code == 500 and response.json().get('type') == 'RuntimeError', "stopped gateway cannot pass health")
        else:
            print("[SKIP] real gateway lifecycle: no OPENCLAW_GATEWAY_TOKEN; not model acceptance", flush=True)
        response = client.post("/shell", json={"command": "printf openclaw-server-smoke"})
        check(response.status_code == 200 and response.json().get('exit_code') == 0
              and response.json().get('stdout') == 'openclaw-server-smoke', "server shell")
    if os.environ.get("E2E_REQUIRE_LLM") != "1":
        print("[SKIP] actual native model conversations not requested", flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"[FAIL] {type(exc).__name__}: {exc}", flush=True)
        sys.exit(1)
