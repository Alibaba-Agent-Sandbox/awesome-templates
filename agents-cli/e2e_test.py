#!/usr/bin/env python3
"""Actual pinned-CLI diagnostics and restricted HTTP contracts, without model turns.

Fixture adapters are exercised only by test_protocol.py using an explicit test PATH.
This smoke never infers real coding acceptance from a protocol message.
"""
from __future__ import annotations

import os
import sys
import json
import secrets
import time

import httpx

# The host runner passes provider gateway authentication separately from app auth.
import json as _e2e_json
_GATEWAY_HEADERS = _e2e_json.loads(os.environ.get("E2E_GATEWAY_HEADERS_JSON", "{}"))
if not isinstance(_GATEWAY_HEADERS, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in _GATEWAY_HEADERS.items()):
    raise ValueError("E2E_GATEWAY_HEADERS_JSON must be an object of string headers")
_APPLICATION_HEADERS = {"Authorization": "Bearer " + os.environ["ABX_SERVER_TOKEN"]} if os.environ.get("ABX_SERVER_TOKEN") else {}

EXPECTED = "codex 0.162.1; qwen-code 0.23.0"


def check(ok: bool, label: str) -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {label}", flush=True)
    if not ok:
        raise AssertionError(label)


def main() -> int:
    headers = {}
    server_token = os.environ.get("ABX_SERVER_TOKEN", "")
    if server_token:
        headers["Authorization"] = "Bearer " + server_token
    workspace = os.environ.get("E2E_WORKSPACE") or os.environ.get("WORKSPACE") or "/home/user/workspace"
    with httpx.Client(base_url=os.environ.get("E2E_BASE_URL", "http://127.0.0.1:9000"),
                      headers={**(headers), **_GATEWAY_HEADERS, **_APPLICATION_HEADERS}, timeout=60) as client:
        response = client.get("/health")
        check(response.status_code == 200 and response.json().get("status") == "ok", "health")
        response = client.get("/commands")
        check(response.status_code == 200 and
              {item["name"] for item in response.json().get("commands", [])} == {"agents_version", "agents_configure_codex"},
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
            response = httpx.get(str(client.base_url).rstrip("/") + "/commands", timeout=10, headers=_GATEWAY_HEADERS)
            check(response.status_code == 401, "server token protects business routes")
    requested = any(os.environ.get(name, "").lower() in {"1", "true", "yes"}
                    for name in ("E2E_RUN_LLM", "E2E_REQUIRE_LLM"))
    if requested:
        with httpx.Client(base_url=os.environ.get("E2E_BASE_URL", "http://127.0.0.1:9000"),
                          headers={**_GATEWAY_HEADERS, **_APPLICATION_HEADERS}, timeout=60) as client:
            response=client.post('/commands/agents_configure_codex',json={})
            check(response.status_code==200 and response.json()['result']=={'configured':True,'wire_api':'responses','credential_written':False},'explicit native Codex profile without stored key')
            model=os.environ['E2E_MODEL']
            for adapter in ('qwen-code','codex'):
                nonce=secrets.token_hex(16);root=workspace+'/abx_agents_model_'+nonce
                expected='Hello agents '+nonce
                response=client.post('/v1/agents/sessions',json={'adapter':adapter,'agent':{'model':model},'environment':{'type':'self_hosted','workspace_directory':workspace}})
                check(response.status_code==200,adapter+' native model session created')
                session=response.json()['id'];path='/v1/agents/sessions/'+session
                for index,prompt in enumerate([
                    'Create the owned directory '+root+'. Write hello.py there that prints exactly '+expected+'. Run it, and write a nonempty report.md describing the program. Remember validation code '+nonce+'. Preserve unrelated files; actually edit files, not just text.',
                    'In the same owned directory from the previous turn, write followup.txt containing only the validation code I gave earlier, plus a newline. Do not alter other files.']):
                    response=client.post(path+'/events',json={'events':[{'type':'agent.session.input.message','input':[{'role':'user','content':[{'type':'input_text','text':prompt}]}]}]})
                    check(response.status_code==202,adapter+' native turn queued')
                    deadline=time.monotonic()+420;previous_items=0 if index==0 else len(items)
                    while time.monotonic()<deadline:
                        state=client.get(path);state.raise_for_status();state=state.json()
                        if state.get('error') or state.get('status')=='failed':raise AssertionError(adapter+' native session failed')
                        response=client.get(path+'/items',params={'limit':100,'order':'asc'});response.raise_for_status();items=response.json()['data']
                        if state.get('status')=='idle' and len(items)>previous_items:break
                        time.sleep(1)
                    else:raise TimeoutError('owned native turn deadline; destroy sandbox to cancel')
                print('AGENTS_MODEL_PROOF '+json.dumps({'adapter':adapter,'root':root,'session':session,'nonce':nonce,'expected_stdout':expected+'\n'}),flush=True)
                check(True,adapter+' two real native turns on the launched public application; independent host artifact checks still required')
    else:
        print("[SKIP] actual native model turns not requested",flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"[FAIL] HTTP smoke aborted ({type(exc).__name__}); response omitted", flush=True)
        sys.exit(1)
