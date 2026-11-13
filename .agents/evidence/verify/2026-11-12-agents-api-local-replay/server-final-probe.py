import asyncio,importlib.metadata as metadata,inspect,json,os,tempfile
from pathlib import Path
from types import SimpleNamespace
from agent_sandbox import ProviderSandbox
from agent_sandbox.managed_agents import ManagedConfig,ManagedService,ManagedStore
from agent_sandbox.managed_agents.__main__ import load_document
from agent_sandbox.models.managed_instance import worker_environment
from agent_sandbox.models.sandbox import SandboxInfo
from agent_sandbox.providers.alicloud_express.managed import ExpressBackend
from agent_sandbox.transport.config import TransportConfig
EXPECTED='b988d2a76057b6202d836ec329cc0bd90a572b26'
distribution=metadata.distribution('agent-sandbox-client')
direct=json.loads(distribution.read_text('direct_url.json'))
assert direct['url']=='https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/'+EXPECTED+'.tar.gz'
assert direct['subdirectory']=='client-sdk'
assert direct['archive_info']['hashes']['sha256']==os.environ['EXPECTED_SOURCE_SHA256']
assert distribution.version=='0.4.0a7'
assert callable(ProviderSandbox.application_endpoint)
assert 'traffic_access_token' in inspect.signature(ProviderSandbox.application_endpoint).parameters
assert {'instance','instance_env_names'} <= set(ManagedConfig.__dataclass_fields__)
assert os.getuid()!=0
private_value='placeholder-image-private-value'
os.environ['ABX_MANAGED_SANDBOX_ENV_JSON']=json.dumps({'CUSTOM_VALUE':private_value})
config=ManagedConfig.from_dict({'revision':'image-local-check','template':'placeholder-prepared',
 'models':{'image-fixture-model':'qwen-code'},
 'modelEnvAllowlist':['OPENAI_API_KEY','OPENAI_BASE_URL','OPENAI_MODEL'],
 'instance':{'timeout':1200,'cpu':2,'memory':2048,'volume_mounts':{'/data':'placeholder-borrowed'},'metadata':{'purpose':'local-image'}},
 'instanceEnvNames':['CUSTOM_VALUE']})
private=worker_environment(load_document('ABX_MANAGED_SANDBOX_ENV'),config.instance_env_names)
assert private['CUSTOM_VALUE']==private_value
assert config.sessions['maxLifetimeSeconds']==1200
captured={};receipts=[]
class FakeHTTP:
 closed=False
 async def close(self):self.closed=True
class FakeSandboxProtocol:
 async def create(self,body,**kwargs):
  captured['payload']=body.to_create_payload()
  return SandboxInfo(sandboxID='local-image-fixture',templateID='placeholder-prepared',envdAccessToken='placeholder-envd-token',trafficAccessToken='placeholder-traffic-token')
class Reader:
 def __aiter__(self):return self.events()
 async def events(self):yield SimpleNamespace(pid=123,exit_code=None)
 async def cancel(self):pass
class FakeProcessProtocol:
 async def start(self,*args,**kwargs):
  captured['process_env']=kwargs['env'];return Reader()
backend=ExpressBackend({'provider':'alicloud-express','apiKey':'placeholder-provider-key','baseUrl':'https://sandbox.example.invalid','domain':'sandbox.example.invalid','region':'cn-hangzhou'},
 {'apiKey':'placeholder-model-key','baseUrl':'https://models.example.invalid','model':'image-fixture-model','adapter':'qwen-code'},instance_env=private)
http=FakeHTTP()
infra=SimpleNamespace(config=TransportConfig(provider='alicloud-express',sandbox_api_key='placeholder-provider-key',sandbox_base_url='https://sandbox.example.invalid',sandbox_domain='sandbox.example.invalid',region='cn-hangzhou'),http_client=http,sandbox_protocol=FakeSandboxProtocol(),process_protocol=FakeProcessProtocol())
async def local_infrastructure():return infra
backend._infra=local_infrastructure
with tempfile.TemporaryDirectory(prefix='abx-image-state-') as temporary:
 service=ManagedService(ManagedStore('sqlite:///'+str(Path(temporary)/'state.db'),local=True),config)
 status,public,_=service.handle('image-owner','POST','/v1/agents/sessions',{'agent':{'model':'image-fixture-model'}})
 assert status==201
 with service.store.transaction() as tx:saved=tx.get(public['id'],'image-owner')
 assert saved['_settings']['instance']==config.instance
 assert saved['_settings']['instanceEnvNames']==['CUSTOM_VALUE']
 assert private_value not in json.dumps(saved)
 asyncio.run(backend.create(saved,'placeholder-image-app-token',receipts.append))
 assert private_value not in json.dumps(receipts)
 assert private_value not in json.dumps(saved['_settings'])
 assert captured['payload']['timeout']==1200
 assert captured['payload']['cpuCount']==2 and captured['payload']['memoryMB']==2048
 assert captured['payload']['volumeMounts']==[{'name':'placeholder-borrowed','path':'/data'}]
 assert captured['payload']['envVars']['CUSTOM_VALUE']==private_value
 assert captured['payload']['metadata']['purpose']=='local-image'
 assert captured['payload']['metadata']['abx-session']==public['id']
 assert captured['process_env']['CUSTOM_VALUE']==private_value
 assert http.closed

from agent_sandbox import template_contract
from agent_sandbox.template_contract.normalize import parse_yaml_v1
from agent_sandbox.managed_agents.http import TokenAuthenticator,make_server
import httpx,hashlib,threading
assert metadata.version('yamlcore')=='0.1.1'
root=Path(template_contract.__file__).parent
vectors=json.loads((root/'yaml-fixtures.json').read_text())
for item in vectors['valid']:
 assert parse_yaml_v1(item['text'])==item['expected']
for item in vectors['invalid']:
 source=bytes.fromhex(item['hex']) if 'hex' in item else item['repeat']*item['count'] if 'repeat' in item else item['text']
 try:parse_yaml_v1(source)
 except ValueError:pass
 else:raise AssertionError(item['id'])
assert parse_yaml_v1('FLAG: on\nWHEN: 2026-11-12')=={'FLAG':'on','WHEN':'2026-11-12'}
with tempfile.TemporaryDirectory(prefix='abx-image-projection-') as temporary:
 service=ManagedService(ManagedStore('sqlite:///'+str(Path(temporary)/'state.db'),local=True),config)
 token='final-image-test-only-token'
 auth=TokenAuthenticator({'tokens':[{'sha256':hashlib.sha256(token.encode()).hexdigest(),'owner':'image-owner','scopes':['agents:read','agents:write']}]})
 server=make_server(service,auth,port=0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  with httpx.Client(base_url=f'http://127.0.0.1:{server.server_port}',headers={'Authorization':'Bearer '+token},trust_env=False) as api:
   response=api.post('/v1/agents/sessions',json={'agent':{'model':'image-fixture-model'}})
   assert response.status_code==201
   sid=response.json()['id']
   for response in (response,api.get('/v1/agents/sessions/'+sid),api.get('/v1/agents/sessions')):
    assert response.status_code in (200,201)
    value=response.json();value=value['data'][0] if 'data' in value else value
    assert type(value['created_at']) is int and type(value['last_active_at']) is int
    assert value['required_actions']==[] and value['vault_ids']==[]
    assert 'remote_url' not in value['environment']
   with service.store.transaction() as tx:
    stored=tx.get(sid,'image-owner')
    assert type(stored['created_at']) is float and type(stored['last_active_at']) is float
    assert 'required_actions' not in stored and 'vault_ids' not in stored
 finally:
  server.shutdown();server.server_close();thread.join(timeout=3)
print(json.dumps({'scope':'real final image; offline local HTTP/SQLite; in-process native infrastructure fixture; no model/cloud',
 'sourceCommit':EXPECTED,'sourceSha256':direct['archive_info']['hashes']['sha256'],'nonRoot':True,
 'managedInstanceTTLAndPrivateEnv':True,'projectionCreateGetList':True,'internalClockPrecision':True,
 'yamlcore':metadata.version('yamlcore'),'validRawVectors':len(vectors['valid']),'invalidRawVectors':len(vectors['invalid'])}))
