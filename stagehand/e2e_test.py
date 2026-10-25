#!/usr/bin/env python3
"""HTTP contract plus actual optional native browser; real model uses SDK controller."""
import os
import sys
import httpx

# The host runner passes provider gateway authentication separately from app auth.
import json as _e2e_json
_GATEWAY_HEADERS = _e2e_json.loads(os.environ.get("E2E_GATEWAY_HEADERS_JSON", "{}"))
if not isinstance(_GATEWAY_HEADERS, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in _GATEWAY_HEADERS.items()):
    raise ValueError("E2E_GATEWAY_HEADERS_JSON must be an object of string headers")
_APPLICATION_HEADERS = {"Authorization": "Bearer " + os.environ["ABX_SERVER_TOKEN"]} if os.environ.get("ABX_SERVER_TOKEN") else {}


def main():
    failed=0
    def record(ok,label):
        nonlocal failed
        failed+=not ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label}",flush=True)
    headers={}
    if os.environ.get('E2E_TOKEN'):headers['X-Access-Token']=os.environ['E2E_TOKEN']
    if os.environ.get('E2E_SERVER_TOKEN'):headers['Authorization']='Bearer '+os.environ['E2E_SERVER_TOKEN']
    with httpx.Client(base_url=os.environ.get('E2E_BASE_URL','http://127.0.0.1:9000').rstrip('/'),headers={**(headers), **_GATEWAY_HEADERS, **_APPLICATION_HEADERS},timeout=90) as client:
        record(client.get('/health').status_code==200,'health')
        response=client.get('/commands');entries={x['name']:x for x in response.json().get('commands',[])}
        record(response.status_code==200 and set(entries)=={'stagehand','stagehand_version','stagehand_setup_check','stagehand_self_test'},'named command surface')
        types={x['name']:x['type']for x in entries.get('stagehand',{}).get('args',[])}
        record(types.get('task')=='string' and types.get('url')=='string' and types.get('command_timeout')=='integer','typed native parameters')
        for payload in [{},{'task':'x','url':'https://example.invalid','unknown':1},{'task':'x','url':'https://example.invalid','command_timeout':'bad'}]:
            record(client.post('/commands/stagehand',json=payload).status_code==400,'invalid arguments400')
        for payload in [{'task':'','url':'https://example.invalid'},{'task':'x','url':'file:///etc/passwd'}]:
            record(client.post('/commands/stagehand',json=payload).status_code==500,'semantic guard rejects before native model')
        record(client.post('/commands/no_such_command',json={}).status_code==404,'unknown command404')
        setup=client.post('/commands/stagehand_setup_check',json={});state=setup.json().get('result',{})
        record(setup.status_code==200 and state.get('browserbase_account_required') is False and all(type(state.get(x)) is bool for x in ['api_key_set','base_url_set','model_set']),'read-only configuration presence')
        version=client.post('/commands/stagehand_version',json={})
        if version.status_code==200 and version.json().get('result')=='4.3.0':
            record(True,'actual pinned native SDK4.3.0')
            test=client.post('/commands/stagehand_self_test',json={})
            record(test.status_code==200 and test.json().get('result')=='STAGEHAND_NATIVE_OK','actual native local browser/extension/title/PNG and cleanup')
        elif os.environ.get('E2E_REQUIRE_CLI')=='1':record(False,'required native SDK and Chromium')
        else:print('[SKIP] native runtime absent; no cloud/native acceptance inferred',flush=True)
        if not all(state.get(x)for x in ['api_key_set','base_url_set','model_set']):
            missing=client.post('/commands/stagehand',json={'task':'x','url':'https://example.invalid'})
            record(missing.status_code==500 and 'required' in missing.json().get('error',''),'missing model fails explicitly')
        if os.environ.get('E2E_REQUIRE_LLM')=='1':record(False,'required real model needs separate SDK model controller')
        else:print('[SKIP] real model; separate owned SDK controller required',flush=True)
    return int(bool(failed))


if __name__=='__main__':sys.exit(main())
