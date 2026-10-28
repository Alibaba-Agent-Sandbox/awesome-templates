"""Original controllers must distinguish an owned local gateway from local apps."""
import runpy
from pathlib import Path
import pytest

NAMES=['copilot-cli','qm','cline','prime-agent','grok','muse','tau2-bench','appworld']
ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('name',NAMES)
@pytest.mark.parametrize('binding',['missing','wrong-url','wrong-id','no-opt-in','owned','remote'])
def test_original_model_controller_target_binding(name,binding,monkeypatch):
    namespace=runpy.run_path(str(ROOT/name/'e2e_test.py'),run_name='ownership-controller-import')
    method=namespace['model'if name in {'tau2-bench','appworld'}else'model_check']
    base='http://127.0.0.1:50123/sandboxes/owned-sandbox/proxy/9000'
    for k in ['E2E_RUN_LLM','E2E_REQUIRE_LLM','E2E_REMOTE_SANDBOX']:monkeypatch.setenv(k,'1')
    monkeypatch.delenv('E2E_OWNED_SANDBOX_ID',raising=False)
    monkeypatch.delenv('E2E_OWNED_GATEWAY_URL',raising=False)
    if binding!='missing':
        monkeypatch.setenv('E2E_OWNED_SANDBOX_ID','wrong-sandbox'if binding=='wrong-id'else'owned-sandbox')
        monkeypatch.setenv('E2E_OWNED_GATEWAY_URL',base+'/other'if binding=='wrong-url'else base)
    if binding=='no-opt-in':monkeypatch.delenv('E2E_REMOTE_SANDBOX')
    if binding=='remote':base='https://owned-remote.invalid/application'
    observations=[];calls=[]
    method.__globals__['record']=lambda ok,label:observations.append(ok)
    class BoundaryReached(BaseException):pass
    class Response:
        status_code=200
        def json(self):return {}
        def raise_for_status(self):return self
    class Client:
        def post(self,*args,**kwargs):calls.append('post');raise BoundaryReached()
        def get(self,*args,**kwargs):calls.append('get');raise BoundaryReached()
        def delete(self,*args,**kwargs):return Response()
    async def native(*args,**kwargs):calls.append('native');raise BoundaryReached()
    if name in {'tau2-bench','appworld'}:method.__globals__['native']=native
    kwargs={'client':Client(),'workspace':'/owned-workspace','base':base}
    if binding in {'owned','remote'}:
        with pytest.raises(BoundaryReached):method(**kwargs)
        assert calls
    else:
        method(**kwargs)
        assert not calls and observations==[False]


def test_operator_binding_is_not_inherited_and_created_endpoint_must_match(monkeypatch,tmp_path):
    from template_http_acceptance import controller_environment
    source=tmp_path/'example';source.mkdir()
    target='http://127.0.0.1:50123/sandboxes/created-sandbox/proxy/9000?route=owned'
    monkeypatch.setenv('E2E_OWNED_SANDBOX_ID','operator-value')
    monkeypatch.setenv('E2E_OWNED_GATEWAY_URL',target)
    env=controller_environment(source,{9000:target},{},real_usage=True)
    assert 'E2E_OWNED_SANDBOX_ID'not in env and'E2E_OWNED_GATEWAY_URL'not in env
    env=controller_environment(source,{9000:target},{},real_usage=True,owned_sandbox_id='created-sandbox')
    assert env['E2E_OWNED_SANDBOX_ID']=='created-sandbox'and env['E2E_OWNED_GATEWAY_URL']==target
    with pytest.raises(ValueError,match='created sandbox endpoint'):
        controller_environment(source,{9000:target},{},real_usage=True,owned_sandbox_id='different-sandbox')
    with pytest.raises(ValueError,match='real usage'):
        controller_environment(source,{9000:target},{},owned_sandbox_id='created-sandbox')
    with pytest.raises(ValueError):
        controller_environment(source,{9000:target},{},real_usage=True,owned_sandbox_id='../other')


def test_controller_ownership_generator_has_no_drift():
    import subprocess,sys
    result=subprocess.run([sys.executable,str(ROOT/'scripts/sync_controller_ownership.py'),'--check'],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
