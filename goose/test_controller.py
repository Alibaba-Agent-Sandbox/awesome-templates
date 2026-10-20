"""Controller result contracts only; synthetic responses are not L3 evidence."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import httpx
import pytest

spec=importlib.util.spec_from_file_location('goose_controller',Path(__file__).with_name('e2e_test.py'))
controller=importlib.util.module_from_spec(spec);spec.loader.exec_module(controller)


@pytest.mark.parametrize('result,expected',[
    ({'stdout':'done','stderr':'','exit_code':0},True),
    ({'stdout':'failed','stderr':'problem','exit_code':7},False),
    ('legacy string from another agent API',False),
    ({'stdout':'done','stderr':'','exit_code':False},False),
])
def test_coding_uses_goose_structured_process_contract(monkeypatch,result,expected):
    monkeypatch.setenv('E2E_RUN_LLM','1');monkeypatch.setenv('E2E_REQUIRE_LLM','1')
    monkeypatch.setattr(controller,'upload',lambda *_:None)
    observed=[]
    class StopAtResult(BaseException):pass
    def record(ok,label):
        if label.startswith('real coding execution completes'):
            observed.append(ok);raise StopAtResult
    monkeypatch.setattr(controller,'record',record)
    def post(path,**kwargs):
        if path=='/shell':return httpx.Response(200,json={'exit_code':1,'stderr':'AssertionError\nRan 3 tests'})
        assert path=='/commands/goose'
        return httpx.Response(200,json={'result':result})
    client=SimpleNamespace(post=post,delete=lambda *a,**k:httpx.Response(200))
    with pytest.raises(StopAtResult):controller.coding(client,{'api_key_set':True,'base_url_set':True,'model_set':True})
    assert observed==[expected]
