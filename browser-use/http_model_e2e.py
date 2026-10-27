"""Actual browser work through the launched application; no model keys on host."""
import base64,hashlib,importlib.util,json,os,re,secrets,shlex,time
from pathlib import Path

def verify(client,record,kind):
    if os.environ.get('E2E_REMOTE_SANDBOX')!='1':
        record(False,'required browser model needs explicitly owned remote sandbox');return
    nonce=secrets.token_hex(16);root=Path(__file__).parent;path='/home/user/app/owned-browser-model-'+nonce+'.py';pid=None;start=None;artifact=None
    fixture=(root/'model_fixture.py').read_bytes();local='http://127.0.0.1:9011/'+nonce+'/'
    def shell(code):
        r=client.post('/shell',json={'command':'python3 -I -c '+shlex.quote(code),'timeout':30});r.raise_for_status();v=r.json();assert v['exit_code']==0;return v['stdout']
    try:
        r=client.post('/files/upload-stream',json={'path':path,'content_base64':base64.b64encode(fixture).decode()});r.raise_for_status()
        # Refuse an occupied port; never stop a pre-existing listener.
        code='import socket,subprocess,sys,pathlib,json\ns=socket.socket();s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(("0.0.0.0",9011));s.close()\np=subprocess.Popen([sys.executable,'+repr(path)+',"--port","9011","--nonce",'+repr(nonce)+'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True,env={"PATH":"/usr/local/bin:/usr/bin:/bin","LANG":"C.UTF-8"})\nprint(json.dumps({"pid":p.pid,"start":pathlib.Path("/proc/"+str(p.pid)+"/stat").read_text().split(") ",1)[1].split()[19]}))'
        identity=json.loads(shell(code));pid=identity['pid'];start=identity['start'];assert type(pid)is int and pid>1
        def state():return json.loads(shell('import urllib.request;print(urllib.request.urlopen('+repr(local+'state')+',timeout=5).read().decode())'))
        for _ in range(30):
            try:
                if state()=={'count':0,'code':''}:break
            except Exception:pass
            time.sleep(.25)
        else:raise RuntimeError('owned browser fixture readiness')
        record(True,'fresh independent fixture baseline through actual process API')
        if kind=='browser-use':
            expected='browser-receipt-'+nonce
            args={'task':'Click Increment exactly three times, enter '+expected+' into Verification code, then click Submit. Confirm the displayed count and saved code. Use visible browser interactions only; do not change URLs or access state endpoints.','url':local,'max_steps':12,'command_timeout':600};command='browser_use'
        else:
            expected='stagehand-receipt-'+nonce
            args={'task':'Click the Publish receipt button once using the visible browser button. Do not navigate or access state endpoints.','url':local,'extract_instruction':'Read the exact displayed published receipt string. Return only that string in text.','command_timeout':240};command='stagehand'
        response=client.post('/commands/'+command,json=args,timeout=660);response.raise_for_status();value=response.json()['result'];candidate=value['screenshot_path']
        assert re.fullmatch('/home/user/app/'+kind+'-artifacts/[0-9a-f]{32}\\.png',candidate)
        artifact=candidate;r=client.get('/files/download-stream',params={'path':artifact});r.raise_for_status();png=base64.b64decode(r.json()['content_base64']);observed=state()
        spec=importlib.util.spec_from_file_location('actual_browser_validation',root/'model_e2e_test.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        diagnostic={'native_done':value.get('done'),'native_success':value.get('success'),'steps':value.get('steps'),'counter':observed.get('count'),'code_matches':observed.get('code')==expected,'final_url_matches':value.get('final_url')==local,'png_bytes':len(png),'timeout_reported':any('timed out'in str(x).lower()or'timeout'in str(x).lower()for x in value.get('error_summary',[]))}
        print('BROWSER_MODEL_DIAGNOSTIC '+json.dumps(diagnostic,sort_keys=True),flush=True)
        if os.environ.get('E2E_DEBUG_BROWSER_RESULT')=='1':
            # Opt-in operator diagnostics stay in the runner's private HTTP log.
            # The worker redacts its model key/base from native errors.
            print('BROWSER_PRIVATE_RESULT '+json.dumps({'result':value.get('result','')[:2048],
                'errors':value.get('error_summary',[])},ensure_ascii=False),flush=True)
        proof=module.validate(value,observed,png,local,expected)
        record(True,'actual configured native model, fresh exact browser interactions and independently decoded PNG')
        print('BROWSER_MODEL_PROOF '+json.dumps(proof,sort_keys=True),flush=True)
    except Exception as exc:
        record(False,'actual browser-model task failed ('+type(exc).__name__+'); private response omitted')
    finally:
        ok=True
        try:
            if pid is not None:
                code='import os,signal,pathlib,time,json\npid='+str(pid)+';p=pathlib.Path("/proc/"+str(pid));expected='+repr(start)+'\nif p.exists():\n stat=(p/"stat").read_text().split(") ",1)[1].split()\n if stat[19]==expected and stat[0]!="Z":\n  cmd=(p/"cmdline").read_bytes();assert '+repr(path.encode())+' in cmd and '+repr(nonce.encode())+' in cmd\n  os.killpg(pid,signal.SIGTERM)\nfor _ in range(100):\n if not p.exists():break\n stat=(p/"stat").read_text().split(") ",1)[1].split()\n if stat[19]!=expected or stat[0]=="Z":break\n time.sleep(.05)\nelse:raise RuntimeError("owned process remains")\nsocket=__import__("socket");s=socket.socket();s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(("0.0.0.0",9011));s.close();print("OWNED_PROCESS_ABSENT")'
                assert shell(code).strip()=='OWNED_PROCESS_ABSENT'
            for f in [artifact,path]:
                if f:
                    r=client.delete('/files',params={'path':f});assert r.status_code in [200,404]
                    assert shell('import pathlib;assert not pathlib.Path('+repr(f)+').exists();print("ABSENT")').strip()=='ABSENT'
        except Exception:ok=False
        record(ok,'exact owned process identity, listener and browser fixture/artifact files independently absent')
