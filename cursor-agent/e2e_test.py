#!/usr/bin/env python3
"""Target HTTP acceptance; generated code runs only on an explicitly owned cloud target."""
from __future__ import annotations
import base64
import asyncio
import hashlib
import importlib.util
import ipaddress
import json
import os
from pathlib import Path
import shlex
import sys
import uuid
from urllib.parse import urlsplit
import httpx

# The host runner passes provider gateway authentication separately from app auth.
import json as _e2e_json
_GATEWAY_HEADERS = _e2e_json.loads(os.environ.get("E2E_GATEWAY_HEADERS_JSON", "{}"))
if not isinstance(_GATEWAY_HEADERS, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in _GATEWAY_HEADERS.items()):
    raise ValueError("E2E_GATEWAY_HEADERS_JSON must be an object of string headers")
_APPLICATION_HEADERS = {"Authorization": "Bearer " + os.environ["ABX_SERVER_TOKEN"]} if os.environ.get("ABX_SERVER_TOKEN") else {}

RESULTS=[]
INVALID_REQUESTS=[{'prompt':''},{'prompt':'x','command_timeout':'bad'},{'prompt':'x','command_timeout':601},{'prompt':'x','cwd':'/outside-workspace','allow_unsafe_tools':True},{'prompt':'x','command_timeout':True}]
INVALID_REQUESTS=[{**value,'allow_unsafe_tools':True}for value in INVALID_REQUESTS]

def record(ok,label):
    RESULTS.append(bool(ok));print(f"[{'PASS' if ok else 'FAIL'}] {label}",flush=True)

def final_text(value):
    if not isinstance(value,dict)or type(value.get('exit_code'))is not int or value['exit_code']!=0 or value.get('native_completed')is not True:return ''
    if value.get('native_version')!='2026.10.19-6bbf2c4'or value.get('archive_sha256')!='cf80cc18d8b33bf33e762353977ca1868cfc45290c92c0ffdcef83bb8b37b44f':return ''
    if value.get('permission_profile')!='explicit-owned-sandbox-bypass':return ''
    return value.get('stdout','').strip()if isinstance(value.get('stdout'),str)else ''


def native_sdk_command(base,parameters):
    from agent_sandbox.api.server_client import ServerClient
    async def run():
        server=ServerClient(base,token=os.environ.get('E2E_SERVER_TOKEN') or None,timeout=760, headers=_GATEWAY_HEADERS)
        try:return await server.commands.run('agent',timeout=760,**parameters)
        finally:await server.aclose()
    return asyncio.run(run())


def local_target(base):
    host=urlsplit(base).hostname or ''
    if host.lower()in ['localhost','localhost.localdomain']:return True
    try:
        address=ipaddress.ip_address(host)
        mapped=getattr(address,'ipv4_mapped',None)
        return address.is_loopback or address.is_unspecified or bool(mapped and(mapped.is_loopback or mapped.is_unspecified))
    except ValueError:return False


def model_check(client,workspace,base):
    enabled=os.environ.get('E2E_RUN_LLM','0')=='1'
    if not enabled:
        if os.environ.get('E2E_REQUIRE_LLM')=='1':record(False,'real-model acceptance is required')
        else:print('[NOT RUN] native model/source-edit acceptance; requires owned cloud opt-in',flush=True)
        return
    if os.environ.get('E2E_REMOTE_SANDBOX')!='1' or local_target(base):
        record(False,'model-generated code requires an explicitly owned remote sandbox');return
    project=workspace+'/abx_e2e_cursor_'+uuid.uuid4().hex;marker='ABX_E2E_'+uuid.uuid4().hex
    source='def add(a, b):\n    return a - b\n'
    tests='import unittest\nfrom calc import add\nclass TestAdd(unittest.TestCase):\n    def test_positive(self):self.assertEqual(add(2,3),5)\n    def test_negative(self):self.assertEqual(add(-2,-3),-5)\n    def test_zero(self):self.assertEqual(add(0,0),0)\n'
    def read(name):
        r=client.get('/files/download-stream',params={'path':project+'/'+name});r.raise_for_status();return base64.b64decode(r.json()['content_base64'])
    try:
        for name,content in [('calc.py',source),('test_calc.py',tests)]:
            client.post('/files/upload-stream',json={'path':project+'/'+name,'content_base64':base64.b64encode(content.encode()).decode()}).raise_for_status()
        r=client.post('/shell',json={'command':'env -i PATH=/usr/local/bin:/usr/bin:/bin python3 -m unittest -v test_calc.py','cwd':project,'timeout':30})
        before=r.json();reproduced=r.status_code==200 and before.get('exit_code')==1 and 'Ran 3 tests' in before.get('stderr','') and 'AssertionError' in before.get('stderr','')
        record(reproduced,'seeded existing source fails the original independent three-test suite')
        if not reproduced:return
        result=native_sdk_command(base,{'prompt':
            'Fix the existing calc.py so add(a,b) returns their sum. Do not modify test_calc.py. '
            'Use the native tools to edit the existing files and verify the change. '
            'Create report.txt explaining the source change. '
            f'Create acceptance.txt containing exactly {marker} followed by one newline. '
            f'After completing all file changes, reply with exactly {marker}.',
            'cwd':project,'command_timeout':600,'allow_unsafe_tools':True})
        ok=final_text(result)==marker
        record(ok,'actual native BYOK final response and zero exit')
        if not ok:return
        changed=read('calc.py');preserved=read('test_calc.py');report=read('report.txt');acceptance=read('acceptance.txt')
        record(changed!=source.encode(),'existing target source changed')
        record(preserved==tests.encode(),'original independent tests remain byte-for-byte unchanged')
        record(bool(report.strip()),'new agent-authored report downloaded from target')
        record(acceptance==(marker+'\n').encode(),'fresh exact acceptance artifact downloaded from target')
        # Compile target bytes after return; unpredictable ACK prevents early-exit acceptance.
        for original in [True,False]:
            ack='POST_RETURN_'+uuid.uuid4().hex
            code="import contextlib,io,pathlib,sys,types,unittest\np=pathlib.Path("+repr(project)+")\nm=types.ModuleType('calc');sys.modules['calc']=m\nwith contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):\n exec(compile((p/'calc.py').read_bytes(),str(p/'calc.py'),'exec'),m.__dict__)\n"
            if original:
                code+=" t=types.ModuleType('test_calc');exec(compile((p/'test_calc.py').read_bytes(),str(p/'test_calc.py'),'exec'),t.__dict__)\n suite=unittest.TestLoader().loadTestsFromModule(t);assert suite.countTestCases()==3\n result=unittest.TextTestRunner(stream=io.StringIO()).run(suite)\n assert result.testsRun==3 and result.wasSuccessful() and not(result.skipped or result.expectedFailures or result.unexpectedSuccesses)\n"
            else:code+=" assert all(m.add(a,b)==a+b for a,b in [(1543,-271),(0,98765),(-809,611),(0.5,1.25)])\n"
            code+='print('+repr(ack)+')\n'
            r=client.post('/shell',json={'command':'env -i PATH=/usr/local/bin:/usr/bin:/bin python3 -I -c '+shlex.quote(code),'cwd':project,'timeout':30});data=r.json()
            record(r.status_code==200 and data.get('exit_code')==0 and data.get('stdout','').strip()==ack,'post-return '+('original three tests' if original else 'fresh held-out cases')+' pass on cloud target')
    finally:
        code='import pathlib,shutil;p=pathlib.Path('+repr(project)+');shutil.rmtree(p) if p.exists() else None;assert not p.exists();print("CLEAN")'
        r=client.post('/shell',json={'command':'python3 -I -c '+shlex.quote(code),'timeout':30});data=r.json();record(r.status_code==200 and data.get('exit_code')==0 and data.get('stdout','').strip()=='CLEAN','owned project cleanup and absence confirmed')

def safe_diagnostic(text):
    import re
    value={}
    for key in ['stage','native_code','native_subtype','missing_module']:
        match=re.search(r'\b'+key+r'=([A-Za-z0-9_@./-]{1,128})',text)
        if match:value[key]=match[1]
    for key,number in re.findall(r'\b(model_requests|native_tool_calls|native_tool_results|sdk_shell|sdk_upload|sdk_download|completed_responses|failed_responses|upstream_status)=([0-9]{1,6})',text):value[key]=int(number)
    match=re.search(r'failure_counts=(\{[^;\n]{0,2048}\})',text)
    if match:
        try:
            counts=json.loads(match[1])
            if isinstance(counts,dict)and all(re.fullmatch(r'[A-Za-z_0-9]{1,64}',k)and type(v)is int and 0<=v<=32 for k,v in counts.items()):value['failure_counts']=counts
        except (ValueError,TypeError):pass
    return value

def native_auth_check(client,workspace,base):
    if os.environ.get('E2E_REMOTE_SANDBOX')!='1':
        record(False,'original native authentication fixture requires an explicitly owned sandbox target');return
    import uuid
    project=workspace+'/.cursor-auth-'+uuid.uuid4().hex
    payload={'prompt':'Return OWNED_NATIVE_AUTH_CHECK without reading or changing files.','cwd':project,'command_timeout':40,'allow_unsafe_tools':True}
    def shell(code):
        response=client.post('/shell',json={'command':'python3 -c '+shlex.quote(code),'timeout':15});response.raise_for_status();return response.json()
    try:
        seeded=shell('from pathlib import Path;p=Path('+repr(project)+');p.mkdir(mode=0o700);(p/"fixture.txt").write_text("OWNED_AUTH_FIXTURE")');assert seeded.get('exit_code')==0
        response=client.post('/commands/agent',json=payload)
        record(response.status_code==500 and 'category=authentication_refused'in response.json().get('error',''),'actual original invalid-key refusal through HTTP named API')
        try:
            native_sdk_command(base,payload)
        except Exception as exc:
            record('category=authentication_refused'in str(exc),'actual original invalid-key refusal through SDK named API')
        else:record(False,'invalid synthetic key unexpectedly accepted')
        response=client.get('/files/download-stream',params={'path':project+'/fixture.txt'});response.raise_for_status()
        record(base64.b64decode(response.json()['content_base64'])==b'OWNED_AUTH_FIXTURE','native auth refusal preserves owned fixture bytes')
    finally:
        cleanup=shell('import shutil,pathlib;p=pathlib.Path('+repr(project)+');shutil.rmtree(p,ignore_errors=True);assert not p.exists();print("OWNED_AUTH_CLEAN")')
        record(cleanup.get('exit_code')==0 and cleanup.get('stdout','').strip()=='OWNED_AUTH_CLEAN','owned native authentication fixture cleanup')


def main():
    base=os.environ.get('E2E_BASE_URL','http://127.0.0.1:9000').rstrip('/');workspace=os.environ.get('E2E_WORKSPACE',os.environ.get('E2E_BASE_DIR','/home/user/app')).rstrip('/')
    token=os.environ.get('E2E_SERVER_TOKEN','');headers={'Authorization':'Bearer '+token}if token else{}
    with httpx.Client(base_url=base,headers={**(headers), **_GATEWAY_HEADERS, **_APPLICATION_HEADERS},timeout=180)as client:
        response=client.get('/health');record(response.status_code==200 and response.json().get('status')=='ok','HTTP health')
        response=client.get('/commands');names={x.get('name')for x in response.json().get('commands',[])};record({'agent','agent_version','agent_setup_check','agent_native_check'}<=names,'typed named commands discovery')
        response=client.post('/commands/agent_setup_check',json={});state=response.json().get('result',{});record(response.status_code==200 and state.get('mode')=='original-cursor-native'and state.get('requires_unsafe_optin')is True,'read-only native configuration presence')
        required=os.environ.get('E2E_REQUIRE_CLI')=='1'
        if state.get('installed')or required:
            response=client.post('/commands/agent_version',json={});record(response.status_code==200 and response.json().get('result')=='2026.10.19-6bbf2c4','actual pinned original package and native version')
            response=client.post('/commands/agent_native_check',json={});record(response.status_code==200 and response.json().get('result')=={'original_native':True,'headless_print':True,'json_output':True,'explicit_force':True,'contained_workspace':True},'actual original native headless flags')
        else:print('[SKIP] original native package absent in source-only operator environment',flush=True)
        for value in INVALID_REQUESTS+[{'prompt':'valid task'}]:
            response=client.post('/commands/agent',json=value);record(response.status_code in [400,500],'invalid or unapproved argument refused before native model call')
        if os.environ.get('E2E_CURSOR_INVALID_KEY_FIXTURE')=='1':
            record(state.get('api_key_set')is True,'owned synthetic invalid native-key fixture configured')
            native_auth_check(client,workspace,base)
        elif required and os.environ.get('E2E_RUN_LLM','0')!='1':record(False,'required original-native authentication error path fixture absent')
        elif not state.get('api_key_set'):
            response=client.post('/commands/agent',json={'prompt':'key guard','allow_unsafe_tools':True})
            record(response.status_code==500 and 'CURSOR_API_KEY is required'in response.json().get('error',''),'missing-key guard prevents interactive login')
            print('[NOT RUN] actual original native authentication fixture; requires owned cloud opt-in',flush=True)
        model_check(client,workspace,base)
    print(f'SUMMARY {sum(RESULTS)} PASS, {len(RESULTS)-sum(RESULTS)} FAIL; native/model omissions remain explicit',flush=True)
    return 0 if all(RESULTS)else 1

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:
        print('[FAIL] original Cursor controller aborted ('+type(exc).__name__+'); private output omitted',flush=True)
        raise SystemExit(1)
