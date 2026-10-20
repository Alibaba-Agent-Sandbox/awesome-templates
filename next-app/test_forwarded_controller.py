"""Controller failure/ownership regressions only; no provider claims."""
import asyncio
import importlib.util
from pathlib import Path

import httpx
import pytest

spec=importlib.util.spec_from_file_location('forwarded_preview_controller',Path(__file__).with_name('forwarded_e2e_test.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_busy_sandbox_refuses_without_stopping_caller_server():
    class Busy:
        async def run(self,name):
            assert name=='dev_status';return {'running':True}
    with pytest.raises(RuntimeError,match='exclusively owned'):asyncio.run(m.verify_forwarded(Busy()))


@pytest.mark.parametrize('status,body',[(503,'ABX_NEXT_PREVIEW'),(200,'wrong application')])
def test_wrong_forwarded_response_fails_and_removes_only_owned_project(monkeypatch,status,body):
    operations=[]
    class Owned:
        def __init__(self):self.files=self;self.network=self;self.running=False;self.exists_value=False
        async def run(self,name,**args):
            operations.append(name)
            if name=='dev_status':return {'running':self.running}
            if name=='scaffold':self.exists_value=True;self.path=args['path'];return args
            if name=='dev_start':self.running=True;return {'port':3000,'kind':'next','running':True}
            if name=='dev_stop':self.running=False;return {'running':False}
            raise AssertionError(name)
        async def exists(self,path):return self.exists_value
        async def remove(self,path):assert path.endswith('/'+self.path);operations.append('owned-remove');self.exists_value=False
        def get_url(self,port):assert port==3000;return 'https://owned.invalid'
    original=httpx.AsyncClient
    monkeypatch.setattr(m.httpx,'AsyncClient',lambda **kwargs:original(transport=httpx.MockTransport(lambda request:httpx.Response(status,text=body,headers={'Content-Type':'text/html'})),**kwargs))
    with pytest.raises(AssertionError):asyncio.run(m.verify_forwarded(Owned()))
    assert operations[-3:]==['dev_stop','dev_status','owned-remove']
