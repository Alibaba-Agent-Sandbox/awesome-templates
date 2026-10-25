#!/usr/bin/env python3
"""External HTTP and actual native offline/CDP smoke; real model controller is separate."""
import os,sys,httpx

# The host runner passes provider gateway authentication separately from app auth.
import json as _e2e_json
_GATEWAY_HEADERS = _e2e_json.loads(os.environ.get("E2E_GATEWAY_HEADERS_JSON", "{}"))
if not isinstance(_GATEWAY_HEADERS, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in _GATEWAY_HEADERS.items()):
    raise ValueError("E2E_GATEWAY_HEADERS_JSON must be an object of string headers")
_APPLICATION_HEADERS = {"Authorization": "Bearer " + os.environ["ABX_SERVER_TOKEN"]} if os.environ.get("ABX_SERVER_TOKEN") else {}
BASE_URL=os.environ.get('E2E_BASE_URL','http://127.0.0.1:9000').rstrip('/')
FAILED=0

def record(ok,label):
    global FAILED
    FAILED+=not ok;print(('['+'PASS' if ok else '['+'FAIL')+'] '+label,flush=True)

def main():
    headers={}
    if os.environ.get('E2E_TOKEN'):headers['X-Access-Token']=os.environ['E2E_TOKEN']
    if os.environ.get('E2E_SERVER_TOKEN'):headers['Authorization']='Bearer '+os.environ['E2E_SERVER_TOKEN']
    with httpx.Client(base_url=BASE_URL,headers={**(headers), **_GATEWAY_HEADERS, **_APPLICATION_HEADERS},timeout=90) as client:
        record(client.get('/health').status_code==200,'health')
        response=client.get('/commands');entries={x['name']:x for x in response.json().get('commands',[])}
        record(response.status_code==200 and {'browser_use','browser_use_version','browser_use_setup_check','browser_use_self_test'}<=entries.keys(),'registered named commands')
        types={x['name']:x['type'] for x in entries.get('browser_use',{}).get('args',[])}
        record(types.get('task')=='string' and types.get('url')=='string' and types.get('max_steps')=='integer' and types.get('command_timeout')=='integer','typed task/url/steps/deadline')
        for payload in [{},{'task':'x','max_steps':'bad'},{'task':'x','not_an_argument':1}]:record(client.post('/commands/browser_use',json=payload).status_code==400,'invalid arguments400')
        record(client.post('/commands/no_such_command',json={}).status_code==404,'unknown command404')
        setup=client.post('/commands/browser_use_setup_check',json={});state=setup.json().get('result',{})
        record(setup.status_code==200 and isinstance(state,dict),'read-only setup')
        required=os.environ.get('E2E_REQUIRE_CLI')=='1'
        if state.get('installed') and state.get('browser_installed'):
            record(client.post('/commands/browser_use_version',json={}).json().get('result')=='0.13.11','actual package version')
            result=client.post('/commands/browser_use_self_test',json={})
            record(result.status_code==200 and result.json().get('result')=='BROWSER_USE_NATIVE_OK','real native CDP navigation/title/PNG and cleanup')
        elif required:record(False,'required native package and Chromium installed')
        else:print('[SKIP] native runtime; no image/provider acceptance claimed',flush=True)
        if not all(state.get(x) for x in ['api_key_set','base_url_set','model_set']):
            response=client.post('/commands/browser_use',json={'task':'x'})
            record(response.status_code==500 and 'required' in response.json().get('error',''),'missing-model guard')
        if os.environ.get('E2E_REQUIRE_LLM')=='1':record(False,'required actual browser model must use separate SDK model_e2e_test.py')
        else:print('[SKIP] real browser model; separate SDK controller required, no L3 claim',flush=True)
    return int(bool(FAILED))

if __name__=='__main__':sys.exit(main())
