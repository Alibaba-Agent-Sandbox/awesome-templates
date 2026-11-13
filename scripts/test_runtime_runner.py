"""Observable startup ownership, private values and cleanup; no cloud claims."""
import argparse
import asyncio
import importlib.util
import json
import os
import stat
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('runtime_runner', ROOT/'scripts/runtime_runner.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class Client:
    async def discover(self): return {'commands': []}
    async def aclose(self): pass


class Sandbox:
    calls = []
    id = 'fixture-owned-id'
    @classmethod
    async def create(cls, **kwargs):
        cls.calls.append(('create', kwargs))
        kwargs['on_created'](cls.id)
        return cls()
    async def start_server(self, **kwargs):
        self.calls.append(('start', kwargs))
        return Client()
    async def kill(self): self.calls.append(('kill', self.id))
    async def close(self): self.calls.append(('close', self.id))


def arguments(path):
    return argparse.Namespace(template='prepared-template',provider='alicloud-express',timeout=1800,ready_timeout=60,session=str(path))


def test_startup_is_explicit_after_creation_with_private_allowlisted_env(tmp_path, monkeypatch):
    Sandbox.calls=[]
    monkeypatch.setattr(runner, 'START_COMMAND', 'actual command')
    monkeypatch.setattr(runner, 'RUNTIME_ENV_NAMES', ('MODEL_KEY',))
    monkeypatch.setenv('MODEL_KEY', 'private-runtime-fixture')
    monkeypatch.setenv('ALICLOUD_ACCESS_KEY_SECRET', 'must-not-reach-guest')
    monkeypatch.delenv('ABX_SERVER_TOKEN', raising=False)
    path=tmp_path/'session.json'
    result=asyncio.run(runner.launch(arguments(path), Sandbox))
    assert [name for name,_ in Sandbox.calls] == ['create','start','close']
    create=Sandbox.calls[0][1];start=Sandbox.calls[1][1]
    assert set(create['envs']) == {'MODEL_KEY','ABX_SERVER_TOKEN'}
    assert start['env'] == create['envs'] and start['command'] == 'actual command'
    assert start['wait'] is True
    state=json.loads(path.read_text())
    assert stat.S_IMODE(path.stat().st_mode)==0o600
    assert state['status']=='ready' and state['sandbox_id']==result['sandbox_id']
    assert state['application_token']==start['token'] and len(start['token'])>=32
    assert 'application_token' not in result and 'MODEL_KEY' not in path.read_text()
    with pytest.raises(FileExistsError): asyncio.run(runner.launch(arguments(path), Sandbox))
    assert len(Sandbox.calls)==3


def test_startup_failure_deletes_only_owned_instance_and_keeps_recovery_record(tmp_path):
    class Failed(Sandbox):
        calls=[]
        async def start_server(self, **kwargs): raise RuntimeError('private-runtime-fixture')
    path=tmp_path/'session.json'
    with pytest.raises(RuntimeError,match='cleanup result') as error:
        asyncio.run(runner.launch(arguments(path), Failed))
    assert 'private-runtime-fixture' not in str(error.value)
    assert [name for name,_ in Failed.calls]==['create','kill','close']
    assert json.loads(path.read_text())['status']=='deleted-after-failure'


def test_cleanup_failure_is_not_reported_as_deleted(tmp_path):
    class Failed(Sandbox):
        calls=[]
        async def start_server(self, **kwargs): raise RuntimeError('startup failed')
        async def kill(self): raise RuntimeError('private-provider-error')
    path=tmp_path/'session.json'
    with pytest.raises(RuntimeError,match='cleanup is incomplete'):
        asyncio.run(runner.launch(arguments(path), Failed))
    assert json.loads(path.read_text())['status']=='cleanup-required'


def test_generated_launchers_are_standalone_and_current():
    import subprocess
    import sys
    subprocess.run([sys.executable, str(ROOT/'scripts/sync_runtime_runners.py'),'--check'],check=True)
    process=subprocess.run([sys.executable,'-I',str(ROOT/'python-hello/run.py'),'--help'],capture_output=True,text=True)
    assert process.returncode==0 and '--template' in process.stdout
    compile((ROOT/'agents-cli/run.py').read_text(),'agents-cli/run.py','exec')


def test_local_close_failure_preserves_original_cloud_cleanup_result(tmp_path):
    class Failed(Sandbox):
        calls=[]
        async def start_server(self, **kwargs): raise RuntimeError('startup failed')
        async def close(self): raise RuntimeError('transport close failed')
    path=tmp_path/'session.json'
    with pytest.raises(RuntimeError,match='cleanup result'):
        asyncio.run(runner.launch(arguments(path), Failed))
    state=json.loads(path.read_text())
    assert state['status']=='deleted-after-failure'
    assert state['local_close_errors']==['RuntimeError']
