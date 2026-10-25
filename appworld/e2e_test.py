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
        if os.environ.get('E2E_REQUIRE_LLM')=='1':
            record(False,'required original AppWorld model task not enabled')
        else:
            print('[NOT RUN] original AppWorld real-model task; owned cloud opt-in required',flush=True)
        return
    if os.environ.get('E2E_REMOTE_SANDBOX')!='1' or local(base):
        record(False,'original task requires explicitly owned remote sandbox')
        return
    folder=None
    try:
        value=asyncio.run(native(base,'appworld_run',task='',max_steps=40,command_timeout=900))
        path=value.get('artifact_path','')
        prefix=workspace+'/abx_appworld_result_'
        valid=path.startswith(prefix) and re.fullmatch(r'[a-f0-9]{32}/result.bundle',path[len(prefix):]) is not None and value.get('log_path')==path
        record(valid,'actual SDK original runner returns an exact owned encrypted artifact path')
        if not valid:
            return
        folder=path.rsplit('/',1)[0]
        record(value.get('native_version')=='0.1.3.post1' and value.get('source_commit')=='66ad8099e12188ece0d3fe45e661dbc01880813b'
               and value.get('data_sha256')=='fd9f9608c2ec71ed0ac25c3633a738b9129a318a129e31230425b9188e508250'
               and value.get('artifact_encrypted') is True,'native source/data identity and protected encrypted distribution')
        record(value.get('task_completed') is True and all(type(value.get(key)) is int and value[key]>0 for key in ['model_steps','bridge_api_calls','native_api_calls']),
               'real compatible model completes original task through actual native APIs')
        record(value.get('score')==1.0 and value.get('success') is True and type(value.get('num_tests')) is int and value['num_tests']>0
               and value.get('pass_count')==value['num_tests'],'original native evaluator passes every selected task test')
        print('NATIVE_APPWORLD '+json.dumps({key:value[key] for key in ['native_version','source_commit','data_sha256','task','model_steps','bridge_api_calls','native_api_calls','task_completed','score','success','num_tests','pass_count','artifact_bytes','artifact_sha256','artifact_encrypted']},sort_keys=True),flush=True)
        response=client.get('/files/download-stream',params={'path':path})
        response.raise_for_status()
        raw=base64.b64decode(response.json()['content_base64'])
        record(len(raw)==value.get('artifact_bytes') and hashlib.sha256(raw).hexdigest()==value.get('artifact_sha256'),
               'independent encrypted artifact download matches native bytes and SHA256')
        replay=asyncio.run(native(base,'appworld_verify_artifact',path=path,task=value['task']))
        record(replay.get('verified') is True and replay.get('original_evaluator') is True and replay.get('model_credentials_used') is False
               and all(replay.get(key)==value[key] for key in ['score','success','num_tests','pass_count','task']),
               'separate keyless original evaluator reloads saved native databases and reproduces all test counts')
        fresh='POST_RETURN_'+uuid.uuid4().hex
        code='import pathlib,hashlib;p=pathlib.Path('+repr(path)+');assert hashlib.file_digest(p.open("rb"),"sha256").hexdigest()=='+repr(value['artifact_sha256'])+';print('+repr(fresh)+')'
        response=client.post('/shell',json={'command':'python3 -I -c '+shlex.quote(code),'timeout':30})
        result=response.json()
        record(response.status_code==200 and result.get('exit_code')==0 and result.get('stdout','').strip()==fresh,
               'independent post-return encrypted target artifact verified with fresh ACK')
    finally:
        if folder:
            code='import pathlib,shutil;p=pathlib.Path('+repr(folder)+');shutil.rmtree(p);assert not p.exists();print("OWNED_APPWORLD_ABSENT")'
            response=client.post('/shell',json={'command':'python3 -I -c '+shlex.quote(code),'timeout':30})
            result=response.json()
            record(response.status_code==200 and result.get('exit_code')==0 and result.get('stdout','').strip()=='OWNED_APPWORLD_ABSENT',
                   'owned encrypted task-result directory removed and independently absent')


def main():
    base=os.environ.get('E2E_BASE_URL','http://127.0.0.1:9000').rstrip('/')
    workspace=os.environ.get('E2E_WORKSPACE','/home/user/workspace').rstrip('/')
    token=os.environ.get('ABX_SERVER_TOKEN','')
    with httpx.Client(base_url=base,headers={**({'Authorization':'Bearer '+token} if token else {}), **_GATEWAY_HEADERS, **_APPLICATION_HEADERS},timeout=150) as client:
        response=client.get('/health')
        record(response.status_code==200 and response.json().get('status')=='ok','HTTP health')
        response=client.get('/commands')
        names={item['name'] for item in response.json().get('commands',[])}
        record({'appworld_version','appworld_setup_check','appworld_native_smoke','appworld_run','appworld_verify_artifact'}<=names,
               'original native engine command discovery')
        response=client.post('/commands/appworld_setup_check',json={})
        record(response.status_code==200 and response.json().get('result',{}).get('mode')=='original-appworld-engine-authored-model-bridge',
               'read-only model setup presence without model request')
        response=client.post('/commands/appworld_version',json={})
        if response.status_code!=200 and os.environ.get('E2E_REQUIRE_CLI')!='1':
            print('[SKIP] native AppWorld environment absent in source-only local check',flush=True)
        else:
            version=response.json().get('result',{})
            record(response.status_code==200 and version.get('native_version')=='0.1.3.post1' and version.get('protected_bundles_encrypted') is True,
                   'actual pinned original package and encrypted data identity')
            observed=asyncio.run(native(base,'appworld_native_smoke'))
            record(observed=='original AppWorld0.1.3.post1 native API and private cleanup OK',
                   'actual original engine task initialization and native API smoke')
        for params in [{'task':'../outside'},{'max_steps':0},{'command_timeout':1},{'max_steps':True}]:
            response=client.post('/commands/appworld_run',json=params)
            record(response.status_code in [400,500],'invalid task request rejected before any model call')
        model(client,base,workspace)
    print('SUMMARY',sum(RESULTS),'PASS,',len(RESULTS)-sum(RESULTS),'FAIL; model omissions explicit',flush=True)
    return 0 if all(RESULTS) else 1


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        text=str(exc)
        stage=re.search(r'private diagnostics omitted; ([a-z_]{1,40}) \(([A-Za-z_][A-Za-z0-9_]{0,63})\)',text)
        counters={key:int(value)for key,value in re.findall(r'\b(model_steps|bridge_api_calls|native_api_calls|tool_validation_failures|empty_model_responses|native_api_errors|deferred_tool_batches|http_status|native_exit_code)=([0-9]{1,6})',text)}
        reason=re.search(r'\bnative_reason=(context_bound|empty_choices|tool_batch_bound|tool_argument_bound|task_incomplete|native_api_log_empty|unclassified)\b',text)
        safe=('; native_stage='+stage[1]+'; native_kind='+stage[2])if stage else''
        if reason:safe+='; native_reason='+reason[1]
        print('[FAIL] original AppWorld controller aborted ('+type(exc).__name__+')'+safe+'; counters='+json.dumps(counters,sort_keys=True)+'; protected content omitted',flush=True)
        raise SystemExit(1)
