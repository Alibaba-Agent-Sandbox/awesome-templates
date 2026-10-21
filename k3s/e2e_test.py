#!/usr/bin/env python3
"""Actual original control-plane checks require an explicitly owned remote target."""
import asyncio,ipaddress,json,os,uuid
from urllib.parse import urlsplit
import httpx
RESULTS=[]
SHA='92b94582eb7b34a8cf532e6006842b9ed215a6783cf56a3dd6271fd35243b2c0'

def record(ok,label):RESULTS.append(bool(ok));print(f"[{'PASS'if ok else'FAIL'}] {label}",flush=True)

def local_target(base):
    host=urlsplit(base).hostname or''
    if host.lower()in ['localhost','localhost.localdomain']:return True
    try:
        address=ipaddress.ip_address(host);mapped=getattr(address,'ipv4_mapped',None)
        return address.is_loopback or address.is_unspecified or bool(mapped and(mapped.is_loopback or mapped.is_unspecified))
    except ValueError:return False

def identity(value):
    return isinstance(value,dict)and value.get('mode')=='original-k3s-agentless-validation'and value.get('native_version')=='v1.37.1+k3s1'and value.get('native_sha256')==SHA and type(value.get('valid'))is bool

def cleaned(value):return all(value.get(key)is True for key in ['api_server_stopped','private_state_removed','node_state_restored'])

def native(client,base):
    if os.environ.get('E2E_REMOTE_SANDBOX')!='1'or local_target(base):record(False,'original control plane requires an explicitly owned remote sandbox');return
    before=client.post('/commands/k3s_setup_check',json={});record(before.status_code==200 and before.json().get('result',{}).get('node_state_empty')is True,'initial owned native node directory is empty')
    name='abx-validate-'+uuid.uuid4().hex
    manifest=json.dumps({'apiVersion':'v1','kind':'Namespace','metadata':{'name':name}})
    from agent_sandbox.api.server_client import ServerClient
    async def sdk():
        server=ServerClient(base,token=os.environ.get('E2E_SERVER_TOKEN')or None,timeout=330)
        try:return await server.commands.run('validate_manifest',manifest_yaml=manifest,command_timeout=180,timeout=300)
        finally:await server.aclose()
    result=asyncio.run(sdk())
    record(identity(result)and result.get('valid')is True,'actual original server-side strict dry-run through SDK named API')
    record(result.get('object',{}).get('kind')=='Namespace'and result.get('object',{}).get('metadata',{}).get('name')==name,'original fresh requested Namespace returned')
    record(result.get('api_ready')is True and result.get('post_api_ready')is True,'original API ready before and after valid manifest')
    record(type(result.get('runtime_uid'))is int and result['runtime_uid']>0 and result.get('worker_nodes')==0,'non-root original control plane has zero worker nodes')
    record(result.get('probe_not_persisted')is True,'fresh original dry-run Namespace independently NotFound afterward')
    record(cleaned(result),'valid operation native server listener and private/node state cleanup')
    invalid=json.dumps({'apiVersion':'v1','kind':'Service','metadata':{'name':'abx-invalid-'+uuid.uuid4().hex},'spec':{'ports':'invalid-type'}})
    response=client.post('/commands/validate_manifest',json={'manifest_yaml':invalid,'command_timeout':180});value=response.json().get('result',{})
    record(response.status_code==200 and identity(value)and value.get('valid')is False and value.get('object')is None and bool(value.get('validation_error','').strip()),'actual original strict Service schema error through HTTP named API')
    record(value.get('post_api_ready')is True and value.get('probe_not_persisted')is True,'invalid manifest preserves original API health and dry-run nonpersistence')
    record(type(value.get('runtime_uid'))is int and value['runtime_uid']>0 and value.get('worker_nodes')==0,'invalid operation also has zero non-root worker nodes')
    record(cleaned(value),'invalid operation native server listener and private/node state cleanup')
    after=client.post('/commands/k3s_setup_check',json={});record(after.status_code==200 and after.json().get('result',{}).get('node_state_empty')is True,'independent post-return native node directory absence')

def main():
    base=os.environ.get('E2E_BASE_URL','http://127.0.0.1:9000').rstrip('/');token=os.environ.get('E2E_SERVER_TOKEN','')
    headers={'Authorization':'Bearer '+token}if token else{}
    with httpx.Client(base_url=base,headers=headers,timeout=330)as client:
        response=client.get('/health');record(response.status_code==200 and response.json().get('status')=='ok','HTTP health')
        response=client.get('/commands');record({'validate_manifest','k3s_version','k3s_native_check','k3s_setup_check'}<={x.get('name')for x in response.json().get('commands',[])},'typed native named command discovery')
        response=client.post('/commands/k3s_setup_check',json={});state=response.json().get('result',{})
        record(response.status_code==200 and state.get('mode')=='original-k3s-agentless-validation'and state.get('worker_nodes_supported')is False and state.get('pods_supported')is False and state.get('persistent_cluster')is False,'read-only agentless profile never claims worker or Pod execution')
        if state.get('installed')or os.environ.get('E2E_REQUIRE_CLI')=='1':
            response=client.post('/commands/k3s_version',json={});record(response.status_code==200 and 'k3s version v1.37.1+k3s1'in str(response.json().get('result','')),'actual original hash-pinned native version')
            response=client.post('/commands/k3s_native_check',json={});record(response.status_code==200 and response.json().get('result')=={'original_native':True,'agentless_flag_in_help':False,'private_data':True,'private_kubeconfig':True,'explicit_port':True},'actual original agentless/private-state server flags')
        else:print('[SKIP] original native binary absent in source-only environment',flush=True)
        invalid=[{'manifest_yaml':''},{'manifest_yaml':'x\0y'},{'manifest_yaml':'x'*32769},{'manifest_yaml':True}]
        invalid +=[{'manifest_yaml':'kind: Namespace','command_timeout':value}for value in [29,301,True,'30']]
        for arguments in invalid:
            response=client.post('/commands/validate_manifest',json=arguments);record(response.status_code in [400,500],'invalid manifest/deadline rejected before a native server')
        if os.environ.get('E2E_REQUIRE_K3S')=='1':native(client,base)
        elif os.environ.get('E2E_REQUIRE_CLI')=='1':record(False,'required original agentless validation controller was not enabled')
        else:print('[NOT RUN] original agentless server; requires owned cloud opt-in',flush=True)
    print(f'SUMMARY {sum(RESULTS)} PASS,{len(RESULTS)-sum(RESULTS)} FAIL',flush=True);return int(not all(RESULTS))
if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:print('[FAIL] original K3s controller aborted ('+type(exc).__name__+'); private output omitted',flush=True);raise SystemExit(1)
