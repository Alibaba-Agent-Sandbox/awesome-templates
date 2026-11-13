"""Offline tests for template-owned bootstrap and release boundaries."""
from __future__ import annotations
import copy
import asyncio
from types import SimpleNamespace
import hashlib
import importlib.util
import json
import os
import socket
import subprocess
import sys
import time
import httpx
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, AsyncMock
import yaml

ROOT = Path(__file__).resolve().parents[1]
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module
release = load('agents_release', ROOT / 'scripts/release.py')
bootstrap = load('agents_bootstrap', ROOT / 'server/bootstrap.py')

class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.manifest = yaml.safe_load((ROOT / 'template.yaml').read_text())
        self.env = {'AGENTS_SERVER_IMAGE':'registry.example/team/server:unique', 'ABX_MANAGED_DATABASE_URL':'postgresql://user:secret@database.example/db', 'SANDBOX_API_KEY':'platform-key', 'SANDBOX_BASE_URL':'https://sandbox.example', 'SANDBOX_DOMAIN':'sandbox.example', 'SANDBOX_REGION':'cn-hangzhou', 'OPENAI_API_KEY':'model-key', 'OPENAI_BASE_URL':'https://model.example/v1', 'OPENAI_MODEL':'test-model', 'AGENTS_FC_ROLE_ARN':'acs:ram::123:role/fc'}

    def test_policy_rejects_budget_and_serial_session_conflicts(self):
        release.validate_policy(self.manifest['vars']['policy'])
        for section,key,value in [('sessions','maxConcurrentTurnsPerSession',2),('sessions','idleTimeoutSeconds',4000),('sessions','maxLifetimeSeconds',600),('limits','maxToolSeconds',601),('limits','maxRunSeconds',False),('storage','unknown',1),('instance','env',{})]:
            with self.subTest(key=key):
                policy=copy.deepcopy(self.manifest['vars']['policy']);policy[section][key]=value
                with self.assertRaises(release.ReleaseError): release.validate_policy(policy)

    def test_init_reuses_private_tokens_and_pending_revision_without_cloud(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); private=root/'.abx/agents-api'
            (root/'template.yaml').write_text(yaml.safe_dump(self.manifest))
            with patch.multiple(release,ROOT=root,PRIVATE=private,STATE=private/'release.json'), patch.dict(os.environ,self.env,clear=True), patch.object(release,'FC',side_effect=AssertionError('init must stay local')):
                with release.lock(): release.initialize('agents-api','cn-hangzhou')
                original=release.read(release.STATE); tokens=release.read(private/'credentials.json'); content=(root/'.env').read_text()
                self.assertNotIn('model-key',content);self.assertNotIn('platform-key',content)
                self.assertEqual((root/'.env').stat().st_mode & 0o777,0o600)
                with release.lock(): release.initialize('agents-api','cn-hangzhou')
                self.assertEqual(release.read(release.STATE)['revision'],original['revision'])
                self.assertEqual(release.read(private/'credentials.json'),tokens)
                self.assertNotEqual(tokens['businessKey'],tokens['internalToken'])
                self.assertEqual(release.dotenv()['AGENTS_BUSINESS_SHA256'],hashlib.sha256(tokens['businessKey'].encode()).hexdigest())
                state=release.read(release.STATE);state['status']='requires_reconcile';release.save(release.STATE,state)
                with self.assertRaises(release.ReleaseError):release.initialize('agents-api','cn-hangzhou')

    def test_explicit_auth_is_not_copied_and_internal_rotation_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);private=root/'.abx/agents-api';(root/'template.yaml').write_text(yaml.safe_dump(self.manifest))
            with patch.multiple(release,ROOT=root,PRIVATE=private,STATE=private/'release.json'),patch.dict(os.environ,{**self.env,'AGENTS_BUSINESS_KEY':'b'*40,'AGENTS_INTERNAL_TOKEN':'i'*40},clear=True):
                with release.lock():release.initialize('agents-api','cn-hangzhou')
                self.assertNotIn('b'*40,(root/'.env').read_text());self.assertFalse((private/'credentials.json').exists())
                with patch.dict(os.environ,{'AGENTS_INTERNAL_TOKEN':'x'*40}):
                    with self.assertRaises(release.ReleaseError):release.initialize('agents-api','cn-hangzhou')

    def test_bootstrap_separates_gateway_and_worker_credentials(self):
        env={**self.env,'AGENTS_APPLICATION':'agents-api','AGENTS_REVISION':'rev-one','AGENTS_TEMPLATE':'template-one','AGENTS_MODEL':'test-model','AGENTS_ADAPTER':'qwen-code','ABX_MANAGED_INTERNAL_TOKEN':'i'*40,'AGENTS_BUSINESS_SHA256':'a'*64,'AGENTS_WORKERS_JSON':'{"rev-one":"worker-one","rev-old":"worker-old"}','AGENTS_POLICY_JSON':json.dumps(self.manifest['vars']['policy']),'AGENTS_STATE_ID':'a'*32}
        gateway=bootstrap.compile_environment(env,'gateway'); worker=bootstrap.compile_environment(env,'worker'); dispatcher=bootstrap.compile_environment(env,'dispatcher')
        self.assertEqual(self.manifest['serving']['dispatcher']['props']['environmentVariables']['ABX_MANAGED_FC_ENDPOINT'], 'fcv3.${vars.region}.aliyuncs.com')
        self.assertEqual(set(gateway),{'ABX_MANAGED_CONFIG_JSON','ABX_MANAGED_AUTH_JSON'})
        self.assertNotIn('ABX_MANAGED_MODEL_CONFIG_JSON',dispatcher)
        self.assertEqual(json.loads(worker['ABX_MANAGED_MODEL_CONFIG_JSON'])['apiKey'],'model-key')
        self.assertEqual(json.loads(gateway['ABX_MANAGED_CONFIG_JSON'])['workers']['rev-old'],'worker-old')
        self.assertEqual(json.loads(gateway['ABX_MANAGED_CONFIG_JSON'])['expectedStateId'],'a'*32)
        for role in ('gateway','worker','dispatcher'):
            props=self.manifest['serving'][role]['props']; variables=props['environmentVariables']
            self.assertEqual('OPENAI_API_KEY' in variables,role=='worker')
            self.assertEqual('SANDBOX_API_KEY' in variables,role!='gateway')
            self.assertNotIn('AGENTS_BUSINESS_KEY',variables)

    def test_pinned_sdk_accepts_compiled_policy_and_signed_controls(self):
        from agent_sandbox.managed_agents.models import ManagedConfig
        from agent_sandbox.managed_agents.dispatch import verify_invocation, FCTaskSender
        from agent_sandbox.providers import ManagedExpressBackend
        env={**self.env,'AGENTS_APPLICATION':'agents-api','AGENTS_REVISION':'rev-one','AGENTS_TEMPLATE':'template-one','AGENTS_MODEL':'test-model','AGENTS_ADAPTER':'qwen-code','ABX_MANAGED_INTERNAL_TOKEN':'i'*40,'AGENTS_BUSINESS_SHA256':'a'*64,'AGENTS_WORKERS_JSON':'{"rev-one":"worker-one"}','AGENTS_POLICY_JSON':json.dumps(self.manifest['vars']['policy'])}
        compiled=bootstrap.compile_environment(env,'worker')
        config=ManagedConfig.from_dict(json.loads(compiled['ABX_MANAGED_CONFIG_JSON']))
        self.assertEqual(config.instance['timeout'],3600)
        backend=ManagedExpressBackend(json.loads(compiled['ABX_MANAGED_PROVIDER_CONFIG_JSON']),json.loads(compiled['ABX_MANAGED_MODEL_CONFIG_JSON']))
        self.assertEqual(backend.provider['region'],'cn-hangzhou')
        payload={'operation':'status','applicationId':'agents-api'}
        self.assertEqual(verify_invocation(release.signed(payload,'i'*40),'i'*40,'dispatcher'),payload)
        FCTaskSender('fcv3.cn-hangzhou.aliyuncs.com',config.workers,'i'*40,client=object())

    def test_pinned_backend_creates_with_private_env_then_starts_bridge(self):
        from agent_sandbox.providers import ManagedExpressBackend
        from agent_sandbox.providers.alicloud_express.provider import AlicloudExpressProvider
        order=[]
        provider={'provider':'alicloud-express','apiKey':'sandbox-key','baseUrl':'https://sandbox.example','domain':'sandbox.example','region':'cn-hangzhou'}
        backend=ManagedExpressBackend(provider,{'apiKey':'model-key','baseUrl':'https://model.example/v1','model':'test-model','adapter':'qwen-code'})
        info=SimpleNamespace(sandbox_id='owned-id',envd_access_token='envd-token',traffic_access_token='traffic-token')
        class Reader:
            def __aiter__(self):return self.chunks()
            async def chunks(self):yield SimpleNamespace(pid=12,exit_code=0)
            async def cancel(self):order.append('reader-close')
        async def create(config,**kwargs):
            order.append('create');self.assertEqual(config.env_vars['ABX_SERVER_TOKEN'],'private-token')
            self.assertEqual(config.env_vars['OPENAI_API_KEY'],'model-key');return info
        async def start(*args,**kwargs):
            order.append('start');self.assertEqual(kwargs['env']['ABX_SERVER_TOKEN'],'private-token')
            self.assertIn('agent_sandbox.server.managed',kwargs['args'][1]);return Reader()
        infra=SimpleNamespace(sandbox_protocol=SimpleNamespace(create=create),process_protocol=SimpleNamespace(start=start),http_client=SimpleNamespace(close=AsyncMock()),config=object())
        session={'id':'session-one','_revision':'rev-one','agent':{'model':'test-model','x_agent_sandbox':{'adapter':'qwen-code'}},'_settings':{'template':'template-one','workspace':'/workspace','port':9000,'modelEnvAllowlist':['OPENAI_API_KEY','OPENAI_BASE_URL','OPENAI_MODEL'],'sessions':{'maxLifetimeSeconds':3600},'instance':{'timeout':3600}}}
        def owned(resource):order.append('owned')
        with patch.object(backend,'_infra',AsyncMock(return_value=infra)),patch.object(AlicloudExpressProvider,'application_endpoint',AsyncMock(return_value={'url':'https://bridge.example','headers':{}})),patch.object(AlicloudExpressProvider,'prepare_session',AsyncMock(return_value={'envd_token':'envd-token'})),patch.object(AlicloudExpressProvider,'resolve_session_url',return_value='https://envd.example'):
            result=asyncio.run(backend.create(session,'private-token',owned))
        self.assertEqual(result['sandbox_id'],'owned-id')
        self.assertEqual(order,['create','owned','owned','start','reader-close'])
        infra.http_client.close.assert_awaited_once()
        self.assertNotIn('startCommand',self.manifest['sandbox']['agent']['template'])
        self.assertNotIn('readyCommand',self.manifest['sandbox']['agent']['template'])

    def test_actual_role_entrypoints_health_auth_and_signed_empty_drain(self):
        with tempfile.TemporaryDirectory() as directory:
            env={**self.env,'PATH':os.environ.get('PATH',''),'AGENTS_APPLICATION':'agents-api','AGENTS_REVISION':'rev-one','AGENTS_TEMPLATE':'template-one','AGENTS_MODEL':'test-model','AGENTS_ADAPTER':'qwen-code','ABX_MANAGED_INTERNAL_TOKEN':'i'*40,'AGENTS_BUSINESS_SHA256':hashlib.sha256(('b'*40).encode()).hexdigest(),'AGENTS_WORKERS_JSON':'{"rev-one":"worker-one"}','AGENTS_POLICY_JSON':json.dumps(self.manifest['vars']['policy']),'ABX_MANAGED_DATABASE_URL':'sqlite:///'+str(Path(directory)/'state.sqlite')}
            for role in ('gateway','worker','dispatcher'):
                with socket.socket() as bound:
                    bound.bind(('127.0.0.1',0));port=bound.getsockname()[1]
                process=subprocess.Popen([sys.executable,str(ROOT/'server/bootstrap.py'),role,'--local','--host','127.0.0.1','--port',str(port)],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                try:
                    with httpx.Client(base_url=f'http://127.0.0.1:{port}',trust_env=False,timeout=2) as api:
                        for _ in range(100):
                            if process.poll() is not None:
                                self.fail('role startup failed: '+process.communicate()[1].decode())
                            try:
                                response=api.get('/health')
                                if response.status_code==200:break
                            except httpx.HTTPError:pass
                            time.sleep(0.05)
                        else:self.fail('role health deadline')
                        self.assertEqual(response.json()['mode'],role)
                        self.assertEqual(response.json()['revision'],'rev-one')
                        if role=='gateway':
                            self.assertEqual(api.get('/v1/models').status_code,401)
                            self.assertEqual(api.get('/v1/models',headers={'Authorization':'Bearer '+'b'*40}).status_code,200)
                        if role=='dispatcher':
                            payload={'operation':'drain','applicationId':'agents-api'}
                            result=api.post('/invoke',json=release.signed(payload,'i'*40)).raise_for_status().json()
                            self.assertEqual(len(result['stateInstanceId']),32)
                            self.assertTrue(result['draining'])
                            self.assertEqual([result[k] for k in ('activeSessions','pendingCleanup','uncertainResources')],[0,0,0])
                finally:
                    process.terminate()
                    try:process.communicate(timeout=5)
                    except subprocess.TimeoutExpired:process.kill();process.communicate(timeout=5)

    def test_failed_candidate_keeps_dispatch_but_does_not_publish_alias(self):
        state={'application':'agents-api','region':'cn-hangzhou','status':'preparing','revision':'rev-one','phase':'resources','functions':dict(worker='worker',dispatcher='dispatcher',gateway='gateway'),'previous':{'functions':{'dispatcher':'old-dispatcher'},'version':'previous-version'}}
        calls=[]
        class FakeFC:
            def __init__(self,*args):pass
            def model(self,name,**kwargs):return kwargs
            def control(self,*args):return {'stateInstanceId':'a'*32,'draining':False}
            def patch(self,*args):pass
            def call(self,operation,*args):
                calls.append(operation)
                if operation=='publish_function_version':return {'versionId':'1'}
                raise AssertionError(operation)
            def trigger(self,*args):
                calls.append(('trigger',args[0],args[3],args[4].get('enable')));return {'httpTrigger':{'urlInternet':'https://candidate.example'}}
        with patch.object(release,'read',return_value=state),patch.object(release,'save'),patch.object(release,'write_generated'),patch.object(release,'observed'),patch.object(release,'FC',FakeFC),patch.object(release,'environment',return_value={'AGENTS_INTERNAL_TOKEN':'i'*40,'AGENTS_BUSINESS_KEY':'b'*40}),patch.object(release,'health'),patch.object(release.subprocess,'run') as smoke:
            smoke.return_value.returncode=1
            with self.assertRaises(release.ReleaseError):release.publish()
        self.assertEqual(calls,[('trigger','dispatcher','timer',True),('trigger','old-dispatcher','timer',False),'publish_function_version',('trigger','gateway','http',None)])

    def test_reserve_refuses_unowned_function(self):
        class FakeFC:
            def __init__(self,*args):pass
            def model(self,*args):return {}
            def optional(self,*args):return {'functionId':'other-function'}
        with patch.object(release,'read',return_value={'status':'preparing','region':'cn-hangzhou','functions':{'worker':'existing'}}),patch.object(release,'FC',FakeFC):
            with self.assertRaises(release.ReleaseError):release.reserve('worker')

    def test_control_refuses_replaced_database_before_mutating_drain(self):
        calls=[]
        class FakeFC:
            def __init__(self,*args):pass
            def function(self,*args):return {'functionId':'dispatcher-id'}
            def control(self,name,payload,token):
                calls.append(payload['operation']);return {'stateInstanceId':'b'*32}
        state={'application':'agents-api','region':'cn-hangzhou','functions':{'dispatcher':'dispatcher'},'identities':{'dispatcher':'dispatcher-id'},'stateInstanceId':'a'*32,'drainConfirmed':True}
        with patch.object(release,'read',return_value=state),patch.object(release,'FC',FakeFC),patch.object(release,'environment',return_value={'AGENTS_INTERNAL_TOKEN':'i'*40}),patch.object(release.subprocess,'run') as delete:
            with self.assertRaises(release.ReleaseError):release.destroy()
            delete.assert_not_called()
        self.assertEqual(calls,['status'])

    def test_control_refuses_replaced_function_before_any_signed_request(self):
        class FakeFC:
            def __init__(self,*args):pass
            def function(self,*args):return {'functionId':'replacement'}
            def control(self,*args):raise AssertionError('must not invoke replacement')
        state={'application':'agents-api','region':'cn-hangzhou','functions':{'dispatcher':'dispatcher'},'identities':{'dispatcher':'owned'},'stateInstanceId':'a'*32}
        with patch.object(release,'read',return_value=state),patch.object(release,'FC',FakeFC),patch.object(release,'environment',return_value={'AGENTS_INTERNAL_TOKEN':'i'*40}):
            with self.assertRaises(release.ReleaseError):release.control('drain')

    def test_native_models_and_sdk_call_shape(self):
        from alibabacloud_fc20230330 import models
        from alibabacloud_fc20230330.client import Client
        import inspect
        transport=object.__new__(release.FC);transport.models=models
        request=transport.model('UpdateFunctionRequest',body=transport.model('UpdateFunctionInput',environment_variables={'AGENTS_STATE_ID':'a'*32}))
        self.assertEqual(request.to_map()['body']['environmentVariables'],{'AGENTS_STATE_ID':'a'*32})
        signature=inspect.signature(Client.publish_function_version_with_options)
        self.assertEqual(list(signature.parameters)[-2:],['headers','runtime'])
        signature=inspect.signature(Client.invoke_function_with_options)
        self.assertEqual(list(signature.parameters)[-2:],['headers','runtime'])

if __name__=='__main__':unittest.main()
