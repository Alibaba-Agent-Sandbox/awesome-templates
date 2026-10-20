#!/usr/bin/env python3
"""Real SDK browser-model acceptance inside a supplied owned cloud sandbox.

Borrows that sandbox; kills only its own fixture and command-server processes,
removes its own files, and never destroys the caller's sandbox/template.
"""
import argparse,asyncio,hashlib,io,json,os,re,secrets,shlex,time
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
import httpx
from PIL import Image


def validate(result,state,png,expected_url,code):
    if not isinstance(result,dict) or result.get('done') is not True or result.get('success') is not True:raise AssertionError('native agent did not complete successfully')
    if result.get('final_url')!=expected_url:raise AssertionError('native final URL differs from owned fixture')
    if not isinstance(result.get('result'),str) or not result['result'].strip():raise AssertionError('native final result is empty')
    if not isinstance(state,dict) or type(state.get('count')) is not int or state['count']!=3 or state.get('code')!=code:raise AssertionError('independent fixture state differs from requested browser interactions')
    if type(result.get('bytes')) is not int or result['bytes']!=len(png) or not 1000<len(png)<=16*1024**2:raise AssertionError('independent screenshot length differs')
    with Image.open(io.BytesIO(png)) as image:
        if image.format!='PNG' or image.width<900 or image.height<600:raise AssertionError('independent PNG dimensions/format differ')
        image.verify()
    return {'png_sha256':hashlib.sha256(png).hexdigest(),'png_bytes':len(png),'counter':3,'submitted_code_matches':True,'native_done':True,'native_success':True,'final_url_matches':True}


def _url(base,path):
    value=urlsplit(base);return urlunsplit((value.scheme,value.netloc,value.path.rstrip('/')+'/'+path.lstrip('/'),value.query,''))

async def verify(sb,settings):
    nonce=secrets.token_hex(16);code='browser-code-'+secrets.token_hex(12);path='/home/user/app/abx-browser-model-fixture-'+nonce+'.py';artifact=None;server=None;owned=[];report={'passed':False,'model_acceptance':'NOT_RUN','checks':{}}
    async def launch(command,env):
        stream=await sb.commands.start(command,env=env,timeout=900);entry={'stream':stream,'pid':None,'exited':False};owned.append(entry);event=asyncio.Event()
        async def consume():
            try:
                async for chunk in stream:
                    if chunk.pid:entry['pid']=chunk.pid;event.set()
                    if getattr(chunk,'exit_code',None) is not None:entry['exited']=True
            finally:event.set()
        entry['drain']=asyncio.create_task(consume());await asyncio.wait_for(event.wait(),120)
        if entry['pid'] is None:raise RuntimeError('owned process startup did not return identity')
        return entry
    try:
        await sb.files.write(path,Path(__file__).with_name('model_fixture.py').read_text());report['checks']['fixture_uploaded_via_sdk']=True
        await launch('python3 '+shlex.quote(path)+' --port 9011 --nonce '+nonce,{})
        external=_url(sb.network.get_url(9011),nonce+'/state');local='http://127.0.0.1:9011/'+nonce+'/'
        async with httpx.AsyncClient(timeout=10) as client:
            for _ in range(60):
                try:
                    response=await client.get(external)
                    if response.status_code==200 and response.json()=={'count':0,'code':''}:break
                except (httpx.HTTPError,ValueError):pass
                await asyncio.sleep(1)
            else:raise RuntimeError('owned fixture failed independent SDK-forwarded readiness')
            report['checks']['independent_fixture_baseline']=True
            token=secrets.token_urlsafe(32);env={key:settings[key] for key in ['BROWSER_USE_API_KEY','BROWSER_USE_BASE_URL','BROWSER_USE_MODEL']};env.update(ABX_SERVER_TOKEN=token,WORKSPACE='/home/user/app',HOME='/home/user',PATH='/opt/node/current/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin')
            await launch('agent-sandbox-server serve --port 9010 --commands /home/user/app/commands.py',env)
            server=sb.server_at(9010,token=token)
            for _ in range(60):
                try:
                    if await server.health():break
                except Exception:pass
                await asyncio.sleep(1)
            else:raise RuntimeError('own configured command server failed readiness')
            report['checks']['configured_server_ready']=True
            task='On the current page, click Increment exactly three times, enter '+code+' into Verification code and click Submit. Confirm the count and saved code, then finish with a short summary. Use only the browser interactions; do not change URLs or access fixture state endpoints.'
            result=await server.commands.run('browser_use',task=task,url=local,max_steps=8,command_timeout=300,timeout=360)
            if not isinstance(result,dict):raise AssertionError('native result is not an object')
            candidate=result.get('screenshot_path','')
            if not isinstance(candidate,str) or not re.fullmatch(r'/home/user/app/browser-use-artifacts/[0-9a-f]{32}\.png',candidate):raise AssertionError('native screenshot path is outside owned artifact profile')
            artifact=candidate;png=await sb.files.read_bytes(artifact,max_bytes=16*1024**2);state=(await client.get(external)).json()
            report.update(validate(result,state,png,local,code));report['model_acceptance']='PASS';report['model']=settings['BROWSER_USE_MODEL'];report['passed']=True
    finally:
        cleanup=True
        if server:
            try:await server.aclose()
            except Exception:cleanup=False
        for entry in reversed(owned):
            try:
                if entry['pid'] is not None and not entry['exited']:await sb.commands.kill(entry['pid'])
            except Exception:cleanup=False
            task=entry.get('drain')
            if task:task.cancel();await asyncio.gather(task,return_exceptions=True)
            try:await entry['stream'].cancel()
            except Exception:cleanup=False
        for file in [artifact,path]:
            if file:
                try:await sb.files.remove(file)
                except Exception:cleanup=False
        report['owned_process_file_cleanup_ack']=cleanup
        probe="import socket,json;result=[]\nfor port in [9010,9011]:\n s=socket.socket();s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)\n try:s.bind(('0.0.0.0',port));result.append(True)\n except OSError:result.append(False)\n finally:s.close()\nprint(json.dumps(result))"
        absent=False
        for _ in range(5):
            observed=await sb.commands.run('python3 -I -c '+shlex.quote(probe),timeout=10)
            if observed.exit_code==0 and json.loads(observed.stdout)==[True,True]:absent=True;break
            await asyncio.sleep(.2)
        remaining=await sb.files.list('/home/user/app')
        files_absent=all(getattr(item,'path',None)!=path and getattr(item,'name',None)!=Path(path).name for item in remaining)
        if artifact:
            artifacts=await sb.files.list('/home/user/app/browser-use-artifacts')
            files_absent=files_absent and all(getattr(item,'path',None)!=artifact and getattr(item,'name',None)!=Path(artifact).name for item in artifacts)
        report['owned_listeners_absent']=absent;report['owned_files_absent']=files_absent
        if not cleanup or not absent or not files_absent:raise RuntimeError('owned browser model fixture cleanup not confirmed')
    return report

async def main():
    from agent_sandbox.api.sandbox import Sandbox
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--sandbox-id',required=True);args=parser.parse_args();settings={key:os.environ[key] for key in ['BROWSER_USE_API_KEY','BROWSER_USE_BASE_URL','BROWSER_USE_MODEL']};sb=await Sandbox.connect(args.sandbox_id)
    try:print(json.dumps(await verify(sb,settings),indent=2))
    finally:await sb.close()

if __name__=='__main__':asyncio.run(main())
