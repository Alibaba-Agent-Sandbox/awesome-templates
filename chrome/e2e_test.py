"""External SDK/native CDP/noVNC verification; never infer GUI from a fake PNG."""
import asyncio,base64,hashlib,io,json,os,re,shlex,sys,time,uuid
from pathlib import Path
from urllib.parse import quote,urlsplit,urlunsplit
import httpx
RESULTS=[]


def record(ok,label):RESULTS.append(bool(ok));print(f"[{'PASS'if ok else'FAIL'}] {label}",flush=True)


def visible_fixture_matches(image,expected):
    # Independent observation regions, excluding the initial center cursor and
    # the button reached through actual VNC input.
    positions=[(image.width-100,image.height-100),(image.width-50,image.height//2),(image.width//2,image.height-50)]
    return all(all(abs(value-target)<=4 for value,target in zip(image.getpixel(point)[:3],expected))for point in positions)


async def sdk(base,name,**parameters):
    from agent_sandbox.api.server_client import ServerClient
    client=ServerClient(base,token=os.environ.get('E2E_SERVER_TOKEN')or None,timeout=150)
    try:return await client.commands.run(name,timeout=150,**parameters)
    finally:await client.aclose()


def target_code(client,code):
    response=client.post('/shell',json={'command':'python3 -I -c '+shlex.quote(code),'timeout':30})
    value=response.json()
    if response.status_code!=200 or value.get('exit_code')!=0:raise RuntimeError('independent target observation failed')
    return value.get('stdout','').strip()


async def real_desktop(base,client,headers):
    from cdp import Page
    from rfb import capture_websocket
    from PIL import Image
    ports=[9222,9223,5901,6080]
    baseline=json.loads(target_code(client,'import json,pathlib;print(json.dumps(sorted(str(p)for p in pathlib.Path("/tmp").glob("abx-chrome-*"))))'))
    screenshot=None;started=False
    cdp=os.environ.get('E2E_CHROME_CDP_URL','http://127.0.0.1:9222').rstrip('/')
    vnc=os.environ.get('E2E_CHROME_VNC_URL','http://127.0.0.1:6080').rstrip('/')
    vnc_parts=urlsplit(vnc);ws=urlunsplit(('wss'if vnc_parts.scheme=='https'else'ws',vnc_parts.netloc,'/websockify','',''))
    try:
        value=await sdk(base,'chrome_start');started=value.get('reused')is False
        record(started,'fixture starts a new owned session without adopting an existing browser')
        if not started:return
        password=value.get('vnc_password','')
        record(value.get('running')is True and value.get('headed')is True and value.get('browser_version')=='145.0.7632.6'and value.get('cdp')==9222 and value.get('vnc')==6080,'actual SDK starts headed native Chrome/CDP/noVNC')
        record(len(password)==8 and password.isascii(),'native VNC uses generated password authentication')
        print('NATIVE_CHROME_RESOURCE '+json.dumps({k:value.get(k)for k in ['browser_version','width','height','shm_bytes','memory_limit','cpu_quota','headed']},sort_keys=True),flush=True)
        response=client.get(vnc+'/vnc.html');record(response.status_code==200 and'noVNC'in response.text,'actual upstream noVNC UI is served externally')
        response=client.get(cdp+'/json/version');version=response.json()
        record(response.status_code==200 and'145.0.7632.6'in version.get('Browser','')and'devtools/browser/'in version.get('webSocketDebuggerUrl',''),'forwarded native DevTools discovery and original version')
        marker='CHROME_E2E_'+uuid.uuid4().hex
        html='<!doctype html><html><head><title>'+marker+'</title></head><body style="margin:0;min-height:100vh;background:rgb(230,20,10)"><h1>'+marker+'</h1><button id="action" style="position:absolute;left:30px;top:180px;width:180px;height:70px" onclick="window.n=(window.n||0)+1;document.body.style.background=window.n==1?\'rgb(10,230,20)\':\'rgb(10,20,230)\';this.textContent=String(window.n)">0</button></body></html>'
        async with Page(cdp,headers=headers)as page:
            state=await page.navigate('data:text/html,'+quote(html))
            record(state['title']==marker and await page.evaluate('document.title')==marker,'external original CDP navigates a fresh native fixture')
            native=await page.send('Browser.getVersion');record('145.0.7632.6'in native.get('product',''),'external native WebSocket carries original Browser.getVersion')
            count=await page.evaluate('document.querySelector("#action").click();window.n')
            record(count==1,'external original CDP click changes native DOM state')
            async def frame(pointer=None):
                raw,width,height=await capture_websocket(ws,password,headers=headers,pointer=pointer)
                image=Image.open(io.BytesIO(raw));image.load()
                return raw,width,height,image
            for _ in range(20):
                raw,width,height,image=await frame()
                if visible_fixture_matches(image,(10,230,20)):break
                await asyncio.sleep(.1)
            record((width,height)==(1024,768)and visible_fixture_matches(image,(10,230,20)),'authenticated external noVNC WebSocket RFB shows the same visible CDP state')
            position=await page.evaluate('(()=>{let r=document.querySelector("#action").getBoundingClientRect();return {x:Math.round(screenX+r.x+r.width/2),y:Math.round(screenY+outerHeight-innerHeight+r.y+r.height/2)}})()')
            await frame((position['x'],position['y']))
            for _ in range(30):
                if await page.evaluate('window.n')==2:break
                await asyncio.sleep(.1)
            record(await page.evaluate('window.n')==2,'actual external VNC pointer input reaches the same native browser DOM')
            for _ in range(20):
                raw,width,height,image=await frame()
                if visible_fixture_matches(image,(10,20,230)):break
                await asyncio.sleep(.1)
            record(visible_fixture_matches(image,(10,20,230)),'native desktop redraw after VNC input is visible through VNC')
        artifact=await sdk(base,'chrome_screenshot');candidate=artifact['path']
        workspace=os.environ.get('E2E_WORKSPACE','/home/user/workspace').rstrip('/')
        valid=re.fullmatch(re.escape(workspace)+r'/abx_chrome_capture_[a-f0-9]{32}\.png',candidate)is not None
        record(valid,'native VNC screenshot uses an exclusive owned workspace path')
        if not valid:raise RuntimeError('unexpected screenshot ownership')
        screenshot=candidate
        response=client.get('/files/download-stream',params={'path':screenshot});response.raise_for_status();data=base64.b64decode(response.json()['content_base64'])
        image=Image.open(io.BytesIO(data));image.load();pixel=image.getpixel((image.width//2,image.height//2))
        record(len(data)==artifact['bytes']and hashlib.sha256(data).hexdigest()==artifact['sha256'],'independent downloaded native VNC PNG matches bytes/SHA256')
        record(image.format=='PNG'and image.size==(1024,768)and visible_fixture_matches(image,(10,20,230)),'independently decoded native PNG shows the visible browser result')
        fresh='POST_RETURN_'+uuid.uuid4().hex
        code='import pathlib,hashlib;p=pathlib.Path('+repr(screenshot)+');assert hashlib.file_digest(p.open("rb"),"sha256").hexdigest()=='+repr(artifact['sha256'])+';print('+repr(fresh)+')'
        record(target_code(client,code)==fresh,'post-return exact target PNG verified with unpredictable ACK')
        opened=await sdk(base,'chrome_open',url='about:blank')
        record(opened.get('url')=='about:blank'and opened.get('title')=='','actual SDK valid chrome_open navigates the existing visible native tab')
        async with Page(cdp,headers=headers)as observed:
            record(await observed.evaluate('location.href')=='about:blank'and await observed.evaluate('document.title')=='','independent external CDP confirms the named navigation result')
        again=await sdk(base,'chrome_start');record(again.get('reused')is True,'start is idempotent for the same owned active session')
    finally:
        if screenshot:
            record(target_code(client,'from pathlib import Path;p=Path('+repr(screenshot)+');p.unlink(missing_ok=True);assert not p.exists();print("OWNED_PNG_ABSENT")')=='OWNED_PNG_ABSENT','owned screenshot removal and independent absence')
        if started:
            stopped=await sdk(base,'chrome_stop');record(stopped.get('running')is False and stopped.get('owned_ports_absent')is True,'owned native desktop stop acknowledgement')
            status=await sdk(base,'chrome_status');record(status=={'running':False,'owned_ports_absent':True,'private_state_absent':True},'read-only status confirms stopped owned session')
            code='import json,pathlib,socket\nfor port in '+repr(ports)+':\n s=socket.socket();s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(("0.0.0.0",port));s.close()\nprint(json.dumps(sorted(str(p)for p in pathlib.Path("/tmp").glob("abx-chrome-*"))))'
            record(json.loads(target_code(client,code))==baseline,'independent kernel listeners and private native state absence')


def main():
    base=os.environ.get('E2E_BASE_URL','http://127.0.0.1:9000').rstrip('/');token=os.environ.get('E2E_SERVER_TOKEN','')
    headers={'Authorization':'Bearer '+token}if token else{}
    with httpx.Client(base_url=base,headers=headers,timeout=120)as client:
        response=client.get('/health');record(response.status_code==200 and response.json().get('status')=='ok','HTTP health')
        response=client.get('/commands');names={x['name']for x in response.json().get('commands',[])}
        record({'chrome_version','chrome_setup_check','chrome_start','chrome_status','chrome_open','chrome_screenshot','chrome_stop','chrome_smoke'}<=names,'named browser command discovery')
        response=client.post('/commands/chrome_setup_check',json={});setup=response.json().get('result',{});record(response.status_code==200 and setup.get('mode')=='native-headed-cdp-vnc','read-only native installation inspection')
        for params in [{'url':'file:///etc/passwd'},{'url':'https://u:p@example.invalid'},{'url':'http://remote.invalid:bad'},{'url':'x'*2049}]:
            response=client.post('/commands/chrome_open',json=params);record(response.status_code in [400,500],'invalid browser input rejected without desktop launch')
        if setup.get('installed')is not True:
            if os.environ.get('E2E_REQUIRE_CLI')=='1'or os.environ.get('E2E_REQUIRE_CHROME')=='1':record(False,'required real native Chrome runtime missing')
            else:print('[SKIP] native headed Chrome/CDP/VNC absent in source-only check',flush=True)
        else:
            response=client.post('/commands/chrome_version',json={});record(response.status_code==200 and response.json().get('result',{}).get('browser_version')=='145.0.7632.6','actual pinned native Chrome version')
            asyncio.run(real_desktop(base,client,headers))
    print('SUMMARY',sum(RESULTS),'PASS,',len(RESULTS)-sum(RESULTS),'FAIL; native omissions explicit',flush=True)
    return 0 if all(RESULTS)else 1


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:print('[FAIL] native Chrome controller aborted ('+type(exc).__name__+'); private content omitted',flush=True);raise SystemExit(1)
