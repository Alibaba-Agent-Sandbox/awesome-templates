"""Public managed acceptance retains known ownership through consumer failures."""
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import agent_sandbox
import public_launch_e2e
import verify_managed_templates as managed


def setup(monkeypatch, *, connect_failure=False, kill_failure=False):
    calls=[]
    class CLI:
        def __init__(self, *args): pass
        def run(self, args, **kwargs):
            calls.append(args[0])
            if args[0]=='--version': return 'abx, version 0.5.5'
            if args[0]=='template': return {'sandbox_id':'owned-fixture'}
            if args[0]=='kill' and kill_failure: raise RuntimeError('synthetic CLI failure')
            return '42'
    files=SimpleNamespace(write=AsyncMock(),read=AsyncMock(return_value='owned-proof\n'),
        remove=AsyncMock(),exists=AsyncMock(return_value=False))
    sandbox=SimpleNamespace(id='owned-fixture', files=files, close=AsyncMock(),
        commands=SimpleNamespace(run=AsyncMock(return_value=SimpleNamespace(exit_code=0,stdout=json.dumps({'non_root':True})))))
    connect=AsyncMock(side_effect=RuntimeError('synthetic connect failure')) if connect_failure else AsyncMock(return_value=sandbox)
    monkeypatch.setattr(agent_sandbox,'ProviderSandbox',SimpleNamespace(connect=connect))
    monkeypatch.setattr(public_launch_e2e,'CLI',CLI)
    cleanup=AsyncMock()
    monkeypatch.setattr(public_launch_e2e,'delete_sandbox',cleanup)
    return cleanup,sandbox,calls


def test_connect_failure_still_cleans_id_returned_by_cli(monkeypatch,tmp_path):
    cleanup,_,_=setup(monkeypatch,connect_failure=True)
    assert asyncio.run(managed.verify('base',tmp_path,'fixture-abx')) is False
    assert cleanup.await_args.args[1]=='owned-fixture'
    report=json.loads(next(tmp_path.glob('base-*.json')).read_text())
    assert report['cleanup_verified'] is True and report['passed'] is False


def test_failed_cli_kill_still_attempts_independent_cleanup(monkeypatch,tmp_path):
    cleanup,sandbox,calls=setup(monkeypatch,kill_failure=True)
    assert asyncio.run(managed.verify('base',tmp_path,'fixture-abx')) is False
    cleanup.assert_awaited_once()
    sandbox.close.assert_awaited_once()
    assert 'kill' in calls
    report=json.loads(next(tmp_path.glob('base-*.json')).read_text())
    assert report['cleanup_verified'] is True
    assert report['cli_cleanup_failure_type']=='RuntimeError'
