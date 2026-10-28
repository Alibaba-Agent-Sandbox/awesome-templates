"""External native benchmark acceptance; models run only on an owned remote target."""
import asyncio,base64,hashlib,ipaddress,json,os,re,shlex,uuid
from urllib.parse import urlsplit
import httpx

# The host runner passes provider gateway authentication separately from app auth.
import json as _e2e_json
_GATEWAY_HEADERS = _e2e_json.loads(os.environ.get("E2E_GATEWAY_HEADERS_JSON", "{}"))
if not isinstance(_GATEWAY_HEADERS, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in _GATEWAY_HEADERS.items()):
    raise ValueError("E2E_GATEWAY_HEADERS_JSON must be an object of string headers")
_APPLICATION_HEADERS = {"Authorization": "Bearer " + os.environ["ABX_SERVER_TOKEN"]} if os.environ.get("ABX_SERVER_TOKEN") else {}
RESULTS=[]


# Generated from scripts/sync_controller_ownership.py; do not edit this function alone.
def owned_loopback_gateway(base):
    import re
    sandbox_id=os.environ.get('E2E_OWNED_SANDBOX_ID','')
    bound=os.environ.get('E2E_OWNED_GATEWAY_URL','').rstrip('/')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',sandbox_id) or bound!=base.rstrip('/'):
        return False
    path=urlsplit(base).path.rstrip('/')
    return '/sandboxes/'not in path or path.endswith('/sandboxes/'+sandbox_id+'/proxy/9000')


def record(ok,label):
    RESULTS.append(bool(ok));print(f"[{'PASS'if ok else'FAIL'}] {label}",flush=True)


def local(base):
    host=urlsplit(base).hostname or''
    if host.lower()in ['localhost','localhost.localdomain']:return True
    try:
        value=ipaddress.ip_address(host);mapped=getattr(value,'ipv4_mapped',None)
        return value.is_loopback or value.is_unspecified or bool(mapped and(mapped.is_loopback or mapped.is_unspecified))
    except ValueError:return False


async def native(base,name,**parameters):
    from agent_sandbox.api.server_client import ServerClient
    server=ServerClient(base,token=os.environ.get('ABX_SERVER_TOKEN')or None,timeout=1000, headers=_GATEWAY_HEADERS)
    try:return await server.commands.run(name,timeout=1000,**parameters)
    finally:await server.aclose()


def model(client,base,workspace):
    if os.environ.get('E2E_RUN_LLM')!='1':
        if os.environ.get('E2E_REQUIRE_LLM')=='1':record(False,'required real benchmark model run not enabled')
        else:print('[NOT RUN] actual native agent/user benchmark; owned cloud opt-in required',flush=True)
        return
    if os.environ.get('E2E_REMOTE_SANDBOX')!='1'or (local(base) and not owned_loopback_gateway(base)):record(False,'model benchmark requires explicitly owned remote sandbox');return
    folder=None
    try:
        value=asyncio.run(native(base,'tau2_run',domain='retail',task_id='0',max_steps=40,command_timeout=900))
        path=value.get('artifact_path','');prefix=workspace+'/abx_tau2_result_'
        valid=path.startswith(prefix)and re.fullmatch(r'[a-f0-9]{32}/trajectory.json',path[len(prefix):])is not None and value.get('log_path')==path
        record(valid,'actual SDK native runner returns an exact owned trajectory path')
        if not valid:return
        print('NATIVE_BENCHMARK '+json.dumps({k:value[k]for k in ['native_version','source_commit','domain','task_id','score','termination_reason','message_count','assistant_messages','user_messages','tool_call_count','artifact_bytes','artifact_sha256']},sort_keys=True),flush=True)
        folder=path.rsplit('/',1)[0]
        response=client.get('/files/download-stream',params={'path':path});response.raise_for_status();raw=base64.b64decode(response.json()['content_base64']);artifact=json.loads(raw)
        record(len(raw)==value.get('artifact_bytes')and hashlib.sha256(raw).hexdigest()==value.get('artifact_sha256'),'independent artifact download matches native byte count and SHA256')
        record(artifact.get('source_commit')=='fc0055dc4e0a316c3f83133267fbd6faaa770992'and artifact.get('domain')=='retail'and artifact.get('task_id')=='0','trajectory binds original source and selected official retail task')
        simulation=artifact['simulation'];messages=simulation.get('messages')or[]
        record(simulation.get('termination_reason')in ['agent_stop','user_stop']and value.get('termination_reason')==simulation.get('termination_reason'),'real native simulation completed without timeout/step/error termination')
        record(any(x.get('role')=='assistant'for x in messages)and any(x.get('role')=='user'for x in messages)and any(x.get('tool_calls')for x in messages),'native agent/user conversation contains actual domain tool calls')
        record(value.get('score')==simulation.get('reward_info',{}).get('reward')==1.0,'original native evaluator scored the selected real-model task1.0')
        replay=asyncio.run(native(base,'tau2_verify_artifact',path=path,task_id='0'))
        record(replay.get('replayed')is True and replay.get('score')==value['score']and replay.get('artifact_sha256')==value['artifact_sha256'],'independent keyless upstream strict replay reproduces native reward after return')
        fresh='POST_RETURN_'+uuid.uuid4().hex
        code='import hashlib,pathlib; p=pathlib.Path('+repr(path)+');assert hashlib.file_digest(p.open("rb"),"sha256").hexdigest()=='+repr(value['artifact_sha256'])+';print('+repr(fresh)+')'
        response=client.post('/shell',json={'command':'python3 -I -c '+shlex.quote(code),'timeout':30});data=response.json()
        record(response.status_code==200 and data.get('exit_code')==0 and data.get('stdout','').strip()==fresh,'independent post-return target artifact remains exact with fresh ACK')
    finally:
        if folder:
            code='import pathlib,shutil;p=pathlib.Path('+repr(folder)+');shutil.rmtree(p);assert not p.exists();print("OWNED_TAU2_ABSENT")'
            response=client.post('/shell',json={'command':'python3 -I -c '+shlex.quote(code),'timeout':30});data=response.json();record(response.status_code==200 and data.get('exit_code')==0 and data.get('stdout','').strip()=='OWNED_TAU2_ABSENT','owned trajectory directory cleanup and absence confirmed')


def main():
    base=os.environ.get('E2E_BASE_URL','http://127.0.0.1:9000').rstrip('/');workspace=os.environ.get('E2E_WORKSPACE','/home/user/workspace').rstrip('/');token=os.environ.get('ABX_SERVER_TOKEN','')
    with httpx.Client(base_url=base,headers={**({'Authorization':'Bearer '+token}if token else{}), **_GATEWAY_HEADERS, **_APPLICATION_HEADERS},timeout=40)as client:
        response=client.get('/health');record(response.status_code==200 and response.json().get('status')=='ok','HTTP health')
        response=client.get('/commands');names={x['name']for x in response.json().get('commands',[])};record({'tau2_version','tau2_setup_check','tau2_run','tau2_verify_artifact'}.issubset(names),'native named command discovery')
        response=client.post('/commands/tau2_setup_check',json={});record(response.status_code==200 and response.json().get('result',{}).get('mode')=='native-retail-agent-and-user','read-only setup without model request')
        response=client.post('/commands/tau2_version',json={})
        if response.status_code!=200 and os.environ.get('E2E_REQUIRE_CLI')!='1':print('[SKIP] native Tau2 environment absent in source-only local check',flush=True)
        else:record(response.status_code==200 and response.json().get('result')=={'native_version':'1.0.1','domain':'retail','task_count':114},'actual original native source and114retail tasks')
        for parameters in [{'domain':'unknown'},{'max_steps':0},{'command_timeout':1},{'task_id':'../outside'}]:
            response=client.post('/commands/tau2_run',json=parameters);record(response.status_code in [400,500],'invalid request rejected before any model call')
        model(client,base,workspace)
    print('SUMMARY',sum(RESULTS),'PASS,',len(RESULTS)-sum(RESULTS),'FAIL; model omissions explicit',flush=True)
    return 0 if all(RESULTS)else 1


if __name__=='__main__':raise SystemExit(main())
