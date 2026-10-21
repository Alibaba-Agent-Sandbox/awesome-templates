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

RESULTS=[]
INVALID_REQUESTS=[{'prompt':''},{'prompt':'x','command_timeout':'bad'},{'prompt':'x','command_timeout':601},{'prompt':'x','cwd':'/outside-workspace'},{'prompt':'x','command_timeout':True}]
def record(ok,label):
    RESULTS.append(bool(ok));print(f"[{'PASS' if ok else 'FAIL'}] {label}",flush=True)

def final_text(value):
    if not isinstance(value,dict)or type(value.get('exit_code'))is not int or value['exit_code']!=0 or value.get('native_completed')is not True:return ''
    if value.get('native_version')!='2.0.76'or value.get('cli_sha256')!='45b889599096a2fd6911fdd6ac41d59987b58d04de32e61ea5ec01b28fcc6269':return ''
    if value.get('protocol')!='authored-messages-chat-text-tools':return ''
    if any(type(value.get(key))is not int or value[key]<=0 for key in ['model_calls','native_tool_results']):return ''
    calls=value.get('relay_calls')
    if not isinstance(calls,dict)or type(calls.get('completed_responses'))is not int or calls['completed_responses']<value['model_calls']or type(calls.get('failed_responses'))is not int or calls['failed_responses']!=0:return ''
    return value.get('stdout','').strip()if isinstance(value.get('stdout'),str)else ''


def native_sdk_command(base,parameters):
    from agent_sandbox.api.server_client import ServerClient
    async def run():
        server=ServerClient(base,token=os.environ.get('E2E_SERVER_TOKEN') or None,timeout=760)
        try:return await server.commands.run('claude_byok',timeout=760,**parameters)
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
    project=workspace+'/abx_e2e_claude_'+uuid.uuid4().hex;marker='ABX_E2E_'+uuid.uuid4().hex
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
            'cwd':project,'command_timeout':600})
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
    for key in ['stage','native_code','missing_module']:
        match=re.search(r'\b'+key+r'=([A-Za-z0-9_@./-]{1,128})',text)
        if match:value[key]=match[1]
    for key,number in re.findall(r'\b(model_requests|native_tool_calls|native_tool_results|sdk_shell|sdk_upload|sdk_download)=([0-9]{1,6})',text):value[key]=int(number)
    return value


def main():
    base=os.environ.get('E2E_BASE_URL','http://127.0.0.1:9000').rstrip('/');workspace=os.environ.get('E2E_WORKSPACE','/home/user/app').rstrip('/')
    token=os.environ.get('E2E_SERVER_TOKEN','');headers={'Authorization':'Bearer '+token} if token else {}
    with httpx.Client(base_url=base,headers=headers,timeout=220) as client:
        r=client.get('/health');record(r.status_code==200 and r.json().get('status')=='ok','HTTP health')
        r=client.get('/commands');names={x.get('name') for x in r.json().get('commands',[])};record(r.status_code==200 and {'claude','claude_byok','claude_version','claude_setup_check','claude_native_check'}.issubset(names),'named commands discovery')
        r=client.post('/commands/claude_setup_check',json={});record(r.status_code==200 and r.json().get('result',{}).get('mode')=='original-claude-explicit-chat-adapter','read-only setup check')
        r=client.post('/commands/claude_version',json={})
        if r.status_code!=200 and os.environ.get('E2E_REQUIRE_CLI')!='1':print('[SKIP] native CLI absent in source-only local environment',flush=True)
        else:
            record(r.status_code==200 and r.json().get('result')=='2.0.76 (Claude Code)','actual original Claude ELF SHA256 and native version')
            native=client.post('/commands/claude_native_check',json={})
            record(native.status_code==200 and native.json().get('result')=={'original_native':True,'isolated_settings':True,'no_session_persistence':True,'strict_mcp':True},'actual original headless CLI flags and native executable identity')
        for args in INVALID_REQUESTS:
            r=client.post('/commands/claude_byok',json=args);record(r.status_code in [400,500],'invalid request rejected without native model call')
        model_check(client,workspace,base)
    print(f'SUMMARY {sum(RESULTS)} PASS, {len(RESULTS)-sum(RESULTS)} FAIL; model/native omissions stated separately',flush=True)
    return 0 if all(RESULTS) else 1
if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:
        print('[FAIL] original Claude controller aborted ('+type(exc).__name__+'); diagnostics='+json.dumps(safe_diagnostic(str(exc)),sort_keys=True)+'; private output omitted',flush=True)
        raise SystemExit(1)
