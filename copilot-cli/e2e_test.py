#!/usr/bin/env python3
"""Target HTTP acceptance; generated code runs only on an explicitly owned cloud target."""
from __future__ import annotations
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import sys
import uuid
from urllib.parse import urlsplit
import httpx

RESULTS=[]
def record(ok,label):
    RESULTS.append(bool(ok));print(f"[{'PASS' if ok else 'FAIL'}] {label}",flush=True)

def final_text(stdout):
    final=''
    for line in stdout.splitlines():
        if not line.strip():continue
        try:event=json.loads(line)
        except ValueError:return ''
        if not isinstance(event,dict):return ''
        if event.get('type') in ['session.error','error']:return ''
        if event.get('type')=='assistant.message':
            data=event.get('data')
            if not isinstance(data,dict) or not isinstance(data.get('content'),str):return ''
            final=data['content']
    return final

def model_check(client,workspace,base):
    enabled=os.environ.get('E2E_RUN_LLM','0')=='1'
    if not enabled:
        if os.environ.get('E2E_REQUIRE_LLM')=='1':record(False,'real-model acceptance is required')
        else:print('[NOT RUN] native model/source-edit acceptance; requires owned cloud opt-in',flush=True)
        return
    if os.environ.get('E2E_REMOTE_SANDBOX')!='1' or urlsplit(base).hostname in ['127.0.0.1','localhost','::1']:
        record(False,'model-generated code requires an explicitly owned remote sandbox');return
    project=workspace+'/abx_e2e_copilot_'+uuid.uuid4().hex;marker='ABX_E2E_'+uuid.uuid4().hex
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
        r=client.post('/commands/copilot',json={'prompt':
            'Fix the existing calc.py so add(a,b) returns their sum. Do not modify test_calc.py. '
            'You have file reading/editing/creation tools only; do not request shell execution. '
            'Create report.txt explaining the source change. '
            f'Create acceptance.txt containing exactly {marker} followed by one newline. '
            f'After completing all file changes, reply with exactly {marker}.',
            'cwd':project,'allow_write':True,'command_timeout':600},timeout=660)
        result=r.json().get('result',{});ok=r.status_code==200 and result.get('exit_code')==0 and result.get('native_version')=='1.0.100' and final_text(result.get('stdout','')).strip()==marker
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
    token=os.environ.get('E2E_SERVER_TOKEN','');headers={'Authorization':'Bearer '+token} if token else {}
    with httpx.Client(base_url=base,headers=headers,timeout=30) as client:
        r=client.get('/health');record(r.status_code==200 and r.json().get('status')=='ok','HTTP health')
        r=client.get('/commands');names={x.get('name') for x in r.json().get('commands',[])};record(r.status_code==200 and {'copilot','copilot_version','copilot_setup_check'}.issubset(names),'named commands discovery')
        r=client.post('/commands/copilot_setup_check',json={});record(r.status_code==200 and r.json().get('result',{}).get('mode')=='openai-compatible-byok','read-only setup check')
        r=client.post('/commands/copilot_version',json={})
        if r.status_code!=200 and os.environ.get('E2E_REQUIRE_CLI')!='1':print('[SKIP] native CLI absent in source-only local environment',flush=True)
        else:record(r.status_code==200 and r.json().get('result')=={'native_version':'1.0.100'},'actual pinned native version')
        for args in [{'prompt':''},{'prompt':'x','allow_write':'true'},{'prompt':'x','command_timeout':601},{'prompt':'x','cwd':'/outside-workspace'}]:
            r=client.post('/commands/copilot',json=args);record(r.status_code in [400,500],'invalid request rejected without native model call')
        model_check(client,workspace,base)
    print(f'SUMMARY {sum(RESULTS)} PASS, {len(RESULTS)-sum(RESULTS)} FAIL; model/native omissions stated separately',flush=True)
    return 0 if all(RESULTS) else 1
if __name__=='__main__':raise SystemExit(main())
