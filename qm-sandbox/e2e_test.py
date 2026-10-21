"""Original QM tool context and actual SDK backend HTTP acceptance; no model required."""
import asyncio,base64,hashlib,json,os,shlex,uuid
import httpx
RESULTS=[]


def record(ok,label):
    RESULTS.append(bool(ok));print(f"[{'PASS'if ok else'FAIL'}] {label}",flush=True)


async def sdk(base,name,**parameters):
    from agent_sandbox.api.server_client import ServerClient
    server=ServerClient(base,token=os.environ.get('E2E_SERVER_TOKEN')or None,timeout=230)
    try:return await server.commands.run(name,timeout=230,**parameters)
    finally:await server.aclose()


def backend(client,base,workspace):
    folder='abx_e2e_qm_backend_'+uuid.uuid4().hex;root=workspace+'/'+folder;marker='SDK_NATIVE_'+uuid.uuid4().hex
    code='import pathlib;p=pathlib.Path('+repr(root)+');p.mkdir(mode=0o700);print("OWNED_QM_CREATED")'
    response=client.post('/shell',json={'command':'python3 -I -c '+shlex.quote(code),'timeout':30});value=response.json()
    record(response.status_code==200 and value.get('exit_code')==0 and value.get('stdout','').strip()=='OWNED_QM_CREATED','fresh owned backend project created')
    try:
        result=asyncio.run(sdk(base,'qm_sandbox_file',action='write',path='marker.txt',text=marker,cwd=folder))
        record(result.get('result')is True and result.get('original_qm_tools')is True and result.get('sdk_calls',{}).get('upload')==1,'actual SDK named call executes original QM write through actual Node SDK upload')
        response=client.get('/files/download-stream',params={'path':root+'/marker.txt'});response.raise_for_status()
        data=base64.b64decode(response.json()['content_base64'])
        record(data==marker.encode(),'independent target download matches exact fresh backend bytes')
        result=asyncio.run(sdk(base,'qm_sandbox_file',action='read',path='marker.txt',cwd=folder))
        record(result.get('result',{}).get('content')==marker and result.get('sdk_calls',{}).get('download')==1,'original QM read returns actual SDK-downloaded target content')
        code='from pathlib import Path;assert Path("marker.txt").read_text()=='+repr(marker)+';print("ACTUAL_QM_EXEC_OK")'
        result=asyncio.run(sdk(base,'qm_sandbox_exec',command='python3 -I -c '+shlex.quote(code),cwd=folder,command_timeout=30))
        record(result.get('code')==0 and result.get('stdout','').strip()=='ACTUAL_QM_EXEC_OK'and result.get('timedOut')is False and result.get('original_qm_tools')is True and result.get('sdk_calls',{}).get('shell',0)>=2,'original QM execute uses actual Node SDK and bounded native target process')
        result=asyncio.run(sdk(base,'qm_sandbox_file',action='remove',path='marker.txt',cwd=folder))
        record(result.get('result')is True,'owned backend file removal through actual SDK')
        ack='POST_RETURN_'+uuid.uuid4().hex
        code='import pathlib;p=pathlib.Path('+repr(root)+');assert p.is_dir()and not(p/"marker.txt").exists();print('+repr(ack)+')'
        response=client.post('/shell',json={'command':'python3 -I -c '+shlex.quote(code),'timeout':30});value=response.json()
        record(response.status_code==200 and value.get('exit_code')==0 and value.get('stdout','').strip()==ack,'fresh independent post-return ACK verifies actual owned backend removal')
    finally:
        code='import pathlib,shutil;p=pathlib.Path('+repr(root)+');shutil.rmtree(p)if p.exists()else None;assert not p.exists();print("OWNED_QM_BACKEND_ABSENT")'
        response=client.post('/shell',json={'command':'python3 -I -c '+shlex.quote(code),'timeout':30});value=response.json()
        record(response.status_code==200 and value.get('exit_code')==0 and value.get('stdout','').strip()=='OWNED_QM_BACKEND_ABSENT','owned backend project independently absent')


def main():
    base=os.environ.get('E2E_BASE_URL','http://127.0.0.1:9000').rstrip('/');workspace=os.environ.get('E2E_WORKSPACE','/home/user/app').rstrip('/')
    token=os.environ.get('E2E_SERVER_TOKEN','');headers={'Authorization':'Bearer '+token}if token else{}
    with httpx.Client(base_url=base,headers=headers,timeout=230)as client:
        response=client.get('/health');record(response.status_code==200 and response.json().get('status')=='ok','HTTP health')
        response=client.get('/commands');names={x['name']for x in response.json().get('commands',[])}
        record({'qm_sandbox_version','qm_sandbox_native_check','qm_sandbox_setup_check','qm_sandbox_sdk_smoke','qm_sandbox_exec','qm_sandbox_file'}<=names,'native SDK backend command discovery')
        response=client.post('/commands/qm_sandbox_setup_check',json={})
        record(response.status_code==200 and response.json().get('result',{}).get('mode')=='original-qm-agent-sandbox-sdk-slice','read-only SDK presence without setup/network')
        for request in [{'command':''},{'command':'fixed','command_timeout':0},{'command':'fixed','command_timeout':True},{'command':'fixed','cwd':'/outside-workspace'}]:
            response=client.post('/commands/qm_sandbox_exec',json=request);record(response.status_code in[400,500],'invalid backend request rejected before SDK execution')
        response=client.post('/commands/qm_sandbox_version',json={})
        if response.status_code!=200 and os.environ.get('E2E_REQUIRE_CLI')!='1':print('[SKIP] original QM/SDK environment absent in source-only local check',flush=True)
        else:
            record(response.status_code==200 and response.json().get('result')=={'qm_version':'0.1.0','node_version':'24.16.0','sdk_version':'0.1.0'},'actual original native source/Node/SDK identity')
            result=asyncio.run(sdk(base,'qm_sandbox_native_check'))
            record(result=={'original_qm_harness':True,'original_tool_context':True,'actual_sdk_client':True},'original native harness/tool context and original compiled SDK import')
            result=asyncio.run(sdk(base,'qm_sandbox_sdk_smoke'))
            record(result=='Original QM tools and actual Agent Sandbox SDK round trip/owned cleanup OK','original QM native tool context/real SDK round trip and private cleanup')
            backend(client,base,workspace)
    print('SUMMARY',sum(RESULTS),'PASS,',len(RESULTS)-sum(RESULTS),'FAIL',flush=True)
    return 0 if all(RESULTS)else 1


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:
        print('[FAIL] original QM backend controller aborted ('+type(exc).__name__+'); private output omitted',flush=True)
        raise SystemExit(1)
