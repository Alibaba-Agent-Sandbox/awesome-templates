"""Actual SDK negative paths; no credentials, backend, model or remote resources."""
import asyncio,os
from pathlib import Path
from unittest.mock import patch
import pytest
from agent_sandbox import ProviderSandbox as Sandbox
from agent_sandbox.models.errors import InvalidCredentialsError,ProviderFeatureNotSupportedError
from agent_sandbox.providers.engine_provider import EngineProvider,EngineCodeProtocol
from agent_sandbox.providers.manifest import load_manifest

@pytest.fixture
def source(tmp_path,monkeypatch):
    configured=os.environ.get('E2E_PROVIDER_SOURCE')
    if not configured:pytest.skip('set E2E_PROVIDER_SOURCE to the pinned provider fixture checkout')
    root=Path(configured).resolve()
    assert(root/'e2b/abx-provider.toml').is_file()and(root/'opensandbox/abx-provider.toml').is_file()
    monkeypatch.setenv('HOME',str(tmp_path));monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('ABX_SANDBOX_API_KEY','fixed-synthetic-express-key')
    monkeypatch.setenv('E2B_API_KEY','fixed-synthetic-express-key')
    monkeypatch.delenv('ABX_E2B_API_KEY',raising=False)
    return root

def test_actual_sdk_missing_e2b_specific_key_rejects_before_engine_or_network(source):
    provider=EngineProvider(load_manifest(source/'e2b'),source/'e2b')
    with patch('agent_sandbox.providers.engine_provider.EngineClient',side_effect=AssertionError('must reject before engine/network'))as engine:
        with pytest.raises(InvalidCredentialsError):
            asyncio.run(Sandbox.create(provider=provider,template='desktop',provider_options={'api_key':''}))
        assert engine.call_count==0

def test_actual_sdk_opensandbox_native_interpreter_rejects_before_transport(source):
    provider=EngineProvider(load_manifest(source/'opensandbox'),source/'opensandbox')
    class NoTransport:
        async def call(self,*args,**kwargs):raise AssertionError('unsupported interpreter must not call transport')
    code=EngineCodeProtocol(NoTransport(),'opensandbox',provider.operations)
    with pytest.raises(ProviderFeatureNotSupportedError):
        asyncio.run(code.run_code('engine://owned-fixture','',None,code='print(6*7)'))
