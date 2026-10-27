#!/usr/bin/env python3
"""HTTP contract plus opt-in real desktop acceptance; a skipped GUI is not L1/L2."""
import base64
import hashlib
import json
import os
import struct
import sys
import time
import uuid
from pathlib import PurePosixPath

import httpx

# The host runner passes provider gateway authentication separately from app auth.
import json as _e2e_json
_GATEWAY_HEADERS = _e2e_json.loads(os.environ.get("E2E_GATEWAY_HEADERS_JSON", "{}"))
if not isinstance(_GATEWAY_HEADERS, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in _GATEWAY_HEADERS.items()):
    raise ValueError("E2E_GATEWAY_HEADERS_JSON must be an object of string headers")
_APPLICATION_HEADERS = {"Authorization": "Bearer " + os.environ["ABX_SERVER_TOKEN"]} if os.environ.get("ABX_SERVER_TOKEN") else {}


def main():
    token=os.environ.get('ABX_SERVER_TOKEN','')
    headers={'Authorization':'Bearer '+token} if token else {}
    failures=0
    def check(ok,label):
        nonlocal failures
        failures+=not ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label}",flush=True)
    with httpx.Client(base_url=os.environ.get('E2E_BASE_URL','http://127.0.0.1:9000').rstrip('/'),headers={**(headers), **_GATEWAY_HEADERS, **_APPLICATION_HEADERS},timeout=90) as client:
        response=client.get('/health');check(response.status_code==200,'server health')
        response=client.get('/commands');body=response.json()
        names={c['name'] for c in body.get('commands',[])}
        check(response.status_code==200 and {'osworld_setup_check','desktop_start','desktop_stop','screenshot','click','type','hotkey','a11y_tree','run_task_config','evaluate','osworld_desktop_smoke'}<=names,'typed desktop commands registered')
        response=client.post('/commands/osworld_setup_check',json={});setup=response.json().get('result',{})
        check(response.status_code==200 and setup.get('upstream_commit')=='b138d348256078fa634fc3b73567a7337c793e6b' and setup.get('full_benchmark') is False,'pinned source and explicit browser slice')
        for command,args in [('click',{'x':-1,'y':0}),('type',{'text':''}),('hotkey',{'keys':'ctrl,$(invalid)'})]:
            result=client.post('/commands/'+command,json=args)
            check(result.status_code in (400,500) and result.json().get('type')=='ValueError','invalid '+command+' input fails')
        required=os.environ.get('E2E_REQUIRE_DESKTOP','').lower() in {'1','true','yes'}
        enabled=os.environ.get('E2E_RUN_DESKTOP','').lower() in {'1','true','yes'}
        if required or enabled:
            root=os.environ.get('E2E_WORKSPACE') or os.environ.get('E2E_BASE_DIR','/home/user/app')
            owned=root.rstrip('/')+'/.osworld-http-'+uuid.uuid4().hex
            html_path=owned+'.html';task_path=owned+'.json'
            def call(name,**args):
                result=client.post('/commands/'+name,json=args)
                result.raise_for_status()
                return result.json()['result']
            def upload(path,text):
                result=client.post('/files/upload-stream',json={'path':path,'content_base64':base64.b64encode(text.encode()).decode()})
                result.raise_for_status()
            try:
                result=client.post('/commands/osworld_desktop_smoke',json={})
                check(result.status_code==200 and result.json().get('result')=='desktop screenshot/click/type/hotkey/AT-SPI/evaluation OK','real offline GUI task, upstream observations/evaluator, independent browser state')
                check(call('osworld_setup_check')['running'] is False,'disposable desktop cleaned up')
                html='''<!doctype html><title>External desktop task</title><label for="entry" style="position:absolute;left:100px;top:100px">External task input</label><input id="entry" aria-label="External task input" style="position:absolute;left:100px;top:180px;width:500px;height:60px;font-size:24px"><button style="position:absolute;left:100px;top:300px;width:400px;height:80px" onclick="document.getElementById('result').textContent='Completed '+document.getElementById('entry').value">Apply external task</button><p id="result" role="status" aria-live="polite" style="position:absolute;left:100px;top:450px">Awaiting external input</p>'''
                task={'snapshot':'chrome','config':[{'type':'chrome_open_tabs','parameters':{'urls_to_open':[PurePosixPath(html_path).as_uri()]}}],
                      'evaluator':{'func':'check_include_exclude','result':{'type':'accessibility_tree'},'expected':{'type':'rule','rules':{'include':['Completed external-雪'],'exclude':['Awaiting external input']}}}}
                upload(html_path,html);upload(task_path,json.dumps(task))
                check(call('desktop_start')['running'] is True,'external controller starts a real desktop')
                check('Sandbox desktop ready' in call('a11y_tree'),'observe actual owned welcome page before task navigation')
                applied=call('run_task_config',task_path=task_path)
                check(applied['applied']==1,'uploaded OSWorld task setup applies')
                geometry=applied['browser_geometry']
                offset_x=geometry['content_x'];offset_y=geometry['content_y']
                for _ in range(30):
                    if 'External task input' in call('a11y_tree'):break
                    time.sleep(.1)
                check(call('evaluate',task_path=task_path)['score']==0,'external task baseline evaluates to zero')
                before=call('screenshot');before_png=base64.b64decode(before['base64'],validate=True)
                check(before_png.startswith(b'\x89PNG\r\n\x1a\n') and struct.unpack('>II',before_png[16:24])==(1024,768),'controller independently decodes the real desktop PNG')
                call('click',x=int(offset_x+150),y=int(offset_y+210))
                call('type',text='temporary')
                call('hotkey',keys='ctrl,a')
                call('type',text='external-雪')
                call('click',x=int(offset_x+200),y=int(offset_y+340))
                score=None
                for _ in range(30):
                    score=call('evaluate',task_path=task_path)
                    if score['score']==1:break
                    time.sleep(.1)
                check(score['score']==1 and score['getter']=='accessibility_tree','external GUI actions produce an upstream task score of one')
                observed=False
                for _ in range(30):
                    observed='Completed external-雪' in call('a11y_tree')
                    if observed:break
                    time.sleep(.1)
                check(observed,'fresh real accessibility observation contains the completed state')
                after_png=base64.b64decode(call('screenshot')['base64'],validate=True)
                check(hashlib.sha256(before_png).digest()!=hashlib.sha256(after_png).digest(),'controller independently checks changed screenshot pixels')
            except Exception as exc:
                check(False,'desktop acceptance aborted ('+type(exc).__name__+'); response omitted')
            finally:
                result=client.post('/commands/desktop_stop',json={})
                check(result.status_code==200 and result.json().get('result')=='stopped','owned cleanup is idempotent')
                for path in (task_path,html_path):
                    result=client.delete('/files',params={'path':path})
                    check(result.status_code in (200,404),'owned controller task artifact cleanup')
        else:
            print('[SKIP] GUI task not requested; this HTTP check is not desktop/image/cloud acceptance',flush=True)
    return 1 if failures else 0


if __name__=='__main__':
    sys.exit(main())
