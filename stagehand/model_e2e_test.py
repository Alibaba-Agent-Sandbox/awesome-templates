#!/usr/bin/env python3
"""Real SDK browser-model acceptance inside a supplied owned cloud sandbox.

Borrows that sandbox; kills only its own fixture and command-server processes,
removes its own files, and never destroys the caller's sandbox/template.
"""
import argparse,asyncio,hashlib,io,json,os,re,secrets,shlex
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
import httpx
from PIL import Image


def validate(result,state,png,expected_url,code):
    if not isinstance(result,dict) or result.get('sdk_sha256')!='bdf3cd62126c1529e8a889cae17fd098303e24e962e491a4b20786de72c369e0' or result.get('version')!='4.3.0' or result.get('action',{}).get('success') is not True or not result.get('action',{}).get('actions'):
        raise AssertionError('actual native Stagehand action missing')
    if result.get('final_url')!=expected_url or result.get('extracted',{}).get('text')!=code:
        raise AssertionError('native extraction or final URL differs from fresh receipt')
    if state!={'count':1,'code':code}:raise AssertionError('independent browser click/receipt differs')
    if type(result.get('model_calls')) is not int or not 2<=result['model_calls']<=8:
        raise AssertionError('actual native act/extract inference count differs')
    if type(result.get('png_bytes')) is not int or result['png_bytes']!=len(png) or not 1000<len(png)<=8*1024**2:
        raise AssertionError('independent PNG length differs')
    with Image.open(io.BytesIO(png)) as image:
        if image.format!='PNG' or image.size!=(1024,768):raise AssertionError('independent PNG dimensions/format differ')
        image.verify()
    return {'sdk_sha256':result['sdk_sha256'],'png_sha256':hashlib.sha256(png).hexdigest(),'png_bytes':len(png),'counter':1,'fresh_receipt_matches':True,'native_action_success':True,'native_extraction_matches':True,'final_url_matches':True,'model_calls':result['model_calls']}


def _url(base,path):
    value=urlsplit(base);return urlunsplit((value.scheme,value.netloc,value.path.rstrip('/')+'/'+path.lstrip('/'),value.query,''))

async def verify(sb,settings,diagnostics=None):
    nonce=secrets.token_hex(16);code='stagehand-receipt-'+nonce;path='/home/user/app/abx-stagehand-model-fixture-'+nonce+'.py';artifact=None;server=None;owned=[];report={'passed':False,'model_acceptance':'NOT_RUN','checks':{}}
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
        preflight="import socket\nfor port in [9010,9011]:\n s=socket.socket();s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(('0.0.0.0',port));s.close()\nprint('ABSENT')"
        free=await sb.commands.run('python3 -I -c '+shlex.quote(preflight),timeout=20)
        if free.exit_code!=0 or free.stdout.strip()!='ABSENT':raise RuntimeError('borrowed sandbox required ports are occupied')
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
            token=secrets.token_urlsafe(32);env={key:settings[key] for key in ['STAGEHAND_API_KEY','STAGEHAND_BASE_URL','STAGEHAND_MODEL']};env.update(ABX_SERVER_TOKEN=token,WORKSPACE='/home/user/app',HOME='/home/user',PATH='/opt/node/current/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin')
            await launch('agent-sandbox-server serve --port 9010 --commands /home/user/app/commands.py',env)
            server=sb.server_at(9010,token=token)
            for _ in range(60):
                try:
                    if await server.health():break
                except Exception:pass
                await asyncio.sleep(1)
            else:raise RuntimeError('own configured command server failed readiness')
            report['checks']['configured_server_ready']=True
            task='Click the Publish receipt button once. Use the visible browser button; do not navigate or access state endpoints.'
            report['model_acceptance']='RUNNING'
            result=await server.commands.run('stagehand',task=task,url=local,extract_instruction='Read the exact displayed published receipt string. Return only that string in text.',command_timeout=240,timeout=300)
            if not isinstance(result,dict):raise AssertionError('native result is not an object')
            candidate=result.get('screenshot_path','')
            if not isinstance(candidate,str) or not re.fullmatch(r'/home/user/app/stagehand-artifacts/[0-9a-f]{32}\.png',candidate):raise AssertionError('native screenshot path is outside owned artifact profile')
            artifact=candidate;png=await sb.files.read_bytes(artifact,max_bytes=8*1024**2);state=(await client.get(external)).json()
            report.update(native_action_success=result.get('action',{}).get('success'),model_calls=result.get('model_calls'),independent_counter=state.get('count'),fresh_receipt_matches=state.get('code')==code,final_url_matches=result.get('final_url')==local)
            if diagnostics is not None:diagnostics.update(report)
            report.update(validate(result,state,png,local,code));report['model_acceptance']='PASS';report['model']=settings['STAGEHAND_MODEL'];report['passed']=True
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
            artifacts=await sb.files.list('/home/user/app/stagehand-artifacts')
            files_absent=files_absent and all(getattr(item,'path',None)!=artifact and getattr(item,'name',None)!=Path(artifact).name for item in artifacts)
        report['owned_listeners_absent']=absent;report['owned_files_absent']=files_absent
        if diagnostics is not None:diagnostics.update(report)
        if not cleanup or not absent or not files_absent:raise RuntimeError('owned browser model fixture cleanup not confirmed')
    return report

async def main():
    from agent_sandbox import ProviderSandbox
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--sandbox-id',required=True);args=parser.parse_args();settings={key:os.environ[key] for key in ['STAGEHAND_API_KEY','STAGEHAND_BASE_URL','STAGEHAND_MODEL']};sb=await ProviderSandbox.connect(args.sandbox_id)
    try:print(json.dumps(await verify(sb,settings),indent=2))
    finally:await sb.close()

if __name__=='__main__':asyncio.run(main())
