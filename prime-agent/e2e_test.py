#!/usr/bin/env python3
"""Target HTTP acceptance; generated code runs only on an explicitly owned cloud target."""
from __future__ import annotations
import base64
import asyncio
import ipaddress
import json
import os
import shlex
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
INVALID_REQUESTS=[{'prompt':''},{'prompt':'x','command_timeout':'bad'},{'prompt':'x','command_timeout':601},{'prompt':'x','cwd':'/outside-workspace'}]
def record(ok,label):
    RESULTS.append(bool(ok));print(f"[{'PASS' if ok else 'FAIL'}] {label}",flush=True)

def final_text(stdout):
    try:
        rows=[json.loads(line)for line in stdout.splitlines()if line.strip()]
    except (ValueError,TypeError):
        return ''
    if any(isinstance(row,dict)and row.get('type')=='error'for row in rows):
        return ''
    endings=[row for row in rows if isinstance(row,dict)and row.get('type')=='agent_end']
    turns=[row for row in rows if isinstance(row,dict)and row.get('type')=='turn_end']
    tools=[row for row in rows if isinstance(row,dict)and row.get('type')=='tool_execution_end'and row.get('toolName')=='ipython'and isinstance(row.get('toolCallId'),str)and row['toolCallId']]
    if not endings or not turns or not tools:
        return ''
    messages=endings[-1].get('messages')
    if not isinstance(messages,list):
        return ''
    ids={row['toolCallId']for row in tools}
    if not any(isinstance(message,dict)and message.get('role')=='toolResult'and message.get('toolName')=='ipython'and message.get('toolCallId')in ids and message.get('isError')is False for message in messages):
        return ''
    assistants=[message for message in messages if isinstance(message,dict)and message.get('role')=='assistant']
    if not assistants or assistants[-1].get('stopReason')!='stop':
        return ''
    content=assistants[-1].get('content')
    if not isinstance(content,list):
        return ''
    text=''.join(item.get('text','')for item in content if isinstance(item,dict)and item.get('type')=='text'and isinstance(item.get('text'),str))
    return text.strip()


def native_sdk_command(base,parameters):
    from agent_sandbox.api.server_client import ServerClient
    async def run():
        server=ServerClient(base,token=os.environ.get('ABX_SERVER_TOKEN') or None,timeout=660, headers=_GATEWAY_HEADERS)
        try:return await server.commands.run('prime_agent',timeout=660,**parameters)
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
    project=workspace+'/abx_e2e_prime_agent_'+uuid.uuid4().hex;marker='ABX_E2E_'+uuid.uuid4().hex
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
        ok=result.get('exit_code')==0 and result.get('native_version')=='0.10.0' and result.get('native_completed')is True and final_text(result.get('stdout','')).strip()==marker
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

def main():
    base=os.environ.get('E2E_BASE_URL','http://127.0.0.1:9000').rstrip('/');workspace=os.environ.get('E2E_WORKSPACE','/home/user/app').rstrip('/')
    token=os.environ.get('ABX_SERVER_TOKEN','');headers={'Authorization':'Bearer '+token} if token else {}
    with httpx.Client(base_url=base,headers={**(headers), **_GATEWAY_HEADERS, **_APPLICATION_HEADERS},timeout=90) as client:
        r=client.get('/health');record(r.status_code==200 and r.json().get('status')=='ok','HTTP health')
        r=client.get('/commands');names={x.get('name') for x in r.json().get('commands',[])};record(r.status_code==200 and {'prime_agent','prime_agent_version','prime_agent_kernel_check','prime_agent_setup_check'}.issubset(names),'named commands discovery')
        r=client.post('/commands/prime_agent_setup_check',json={});record(r.status_code==200 and r.json().get('result',{}).get('mode')=='original-native-prime-cpython-repl','read-only setup check')
        r=client.post('/commands/prime_agent_version',json={})
        if r.status_code!=200 and os.environ.get('E2E_REQUIRE_CLI')!='1':print('[SKIP] native CLI absent in source-only local environment',flush=True)
        else:
            record(r.status_code==200 and r.json().get('result')=={'native_version':'0.10.0'},'actual pinned native version')
            response=client.post('/commands/prime_agent_kernel_check',json={})
            record(response.status_code==200 and response.json().get('result')=={'protocol_version':3,'required_imports_checked':12},'actual original native CPython runtime protocol and required imports')
        for args in INVALID_REQUESTS:
            r=client.post('/commands/prime_agent',json=args);record(r.status_code in [400,500],'invalid request rejected without native model call')
        model_check(client,workspace,base)
    print(f'SUMMARY {sum(RESULTS)} PASS, {len(RESULTS)-sum(RESULTS)} FAIL; model/native omissions stated separately',flush=True)
    return 0 if all(RESULTS) else 1
if __name__=='__main__':raise SystemExit(main())
