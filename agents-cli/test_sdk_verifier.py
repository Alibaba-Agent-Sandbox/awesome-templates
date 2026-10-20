"""No-network negative controls for independent coding and owned cleanup gates."""
from __future__ import annotations

import asyncio
import importlib.util
import json
from pathlib import Path
import secrets
import subprocess
import sys
from types import SimpleNamespace

import httpx
import pytest

SPEC = importlib.util.spec_from_file_location('agents_cli_sdk_e2e', Path(__file__).with_name('e2e_sdk.py'))
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

FIXED = '''def fib(n):
    if n < 0:
        raise ValueError('negative')
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a+b
    return a
'''
TESTS = '''import unittest
from fibonacci import fib
class AgentTests(unittest.TestCase):
    def test_positive(self): self.assertEqual(fib(5), 5)
    def test_zero(self): self.assertEqual(fib(0), 0)
    def test_negative(self):
        with self.assertRaises(ValueError): fib(-3)
'''


def invoke(code):
    return subprocess.run([sys.executable, '-I', '-S', '-B', '-c', code],
                          capture_output=True, text=True, timeout=10)


@pytest.fixture
def project(tmp_path):
    root = tmp_path / 'project'
    assert invoke(module.seed_source(str(root))).returncode == 0
    return root


def repaired(root):
    (root / 'fibonacci.py').write_text(FIXED)
    (root / 'test_fibonacci.py').write_text(TESTS)
    (root / 'result.json').write_text(json.dumps(module.ARTIFACT))
    (root / 'report.md').write_text('Fixed Fibonacci and ran both complete unittest modules.')


def check(root, *, suites=True, baseline=False):
    ack = secrets.token_hex(32)
    p = invoke(module.verifier_source(str(root), ack, suites=suites, baseline=baseline))
    return p.returncode == 0 and p.stdout.strip() == ack


def test_real_baseline_and_both_independent_positive_checks(project):
    assert check(project, baseline=True)
    repaired(project)
    assert check(project)
    assert check(project, suites=False)


@pytest.mark.parametrize('case', ['marker-only', 'missing-artifact', 'wrong-artifact', 'empty-report',
    'modified-original', 'no-generated-tests', 'skip', 'expected-failure', 'unexpected-success',
    'sys-exit-zero', 'os-exit-zero', 'keyboard-interrupt', 'old-bytecode', 'symlink-source'])
def test_coding_false_greens_are_rejected(project, case):
    repaired(project)
    if case == 'marker-only':
        (project / 'fibonacci.py').write_text(module.SOURCE)
        (project / 'report.md').write_text('ABX_E2E_OK')
    elif case == 'missing-artifact':
        (project / 'result.json').unlink()
    elif case == 'wrong-artifact':
        (project / 'result.json').write_text('{"fib7":13,"fib10":54}')
    elif case == 'empty-report':
        (project / 'report.md').write_text(' ')
    elif case == 'modified-original':
        (project / 'test_original.py').write_text('import unittest\n')
    elif case == 'no-generated-tests':
        (project / 'test_fibonacci.py').write_text('import unittest\n')
    elif case == 'skip':
        (project / 'test_fibonacci.py').write_text(TESTS.replace('    def test_positive', '    @unittest.skip("skip")\n    def test_positive'))
    elif case == 'expected-failure':
        (project / 'test_fibonacci.py').write_text(TESTS.replace('    def test_positive', '    @unittest.expectedFailure\n    def test_positive').replace('fib(5), 5', 'fib(5), 999'))
    elif case == 'unexpected-success':
        (project / 'test_fibonacci.py').write_text(TESTS.replace('    def test_positive', '    @unittest.expectedFailure\n    def test_positive'))
    elif case == 'sys-exit-zero':
        (project / 'fibonacci.py').write_text('import sys; sys.exit(0)\n')
    elif case == 'os-exit-zero':
        (project / 'fibonacci.py').write_text('import os; os._exit(0)\n')
    elif case == 'keyboard-interrupt':
        (project / 'fibonacci.py').write_text('raise KeyboardInterrupt\n')
    elif case == 'old-bytecode':
        import py_compile
        p = project / 'fibonacci.py'
        py_compile.compile(str(p), cfile=str(project / 'fibonacci.pyc'), doraise=True)
        p.write_text(module.SOURCE)
    elif case == 'symlink-source':
        actual = project / 'actual.py'
        actual.write_text(FIXED)
        (project / 'fibonacci.py').unlink()
        (project / 'fibonacci.py').symlink_to(actual)
    assert not check(project)


def test_baseline_rejects_different_failed_node_with_same_counts(project):
    # Same 1FAIL/1PASS, but zero fails and seven passes.
    (project / 'fibonacci.py').write_text('def fib(n): return 13\n')
    assert not check(project, baseline=True)


@pytest.mark.parametrize('status', ['failed', 'cancelled', 'in_progress'])
def test_native_original_server_state_rejects_noncompleted_turn(tmp_path, status):
    path = tmp_path / 'sessions.json'
    path.write_text(json.dumps({'sessions': [{'id': 'agsess_test', 'turns': [{'status': status, 'error': None}]}]}))
    assert invoke(module.completed_source(str(tmp_path), 'agsess_test', 'unpredictable-test-ack')).returncode != 0


def test_native_state_exact_session_only_and_opaque_ack(tmp_path):
    path = tmp_path / 'sessions.json'
    path.write_text(json.dumps({'sessions': [{'id': 'agsess_other', 'turns': [{'status': 'completed', 'error': None}]}]}))
    assert invoke(module.completed_source(str(tmp_path), 'agsess_test', 'test-ack')).returncode != 0
    path.write_text(json.dumps({'sessions': [{'id': 'agsess_test', 'turns': [{'status': 'completed', 'error': None}]}]}))
    result = invoke(module.completed_source(str(tmp_path), 'agsess_test', 'test-ack'))
    assert result.returncode == 0 and result.stdout.strip() == 'test-ack'


def test_only_selected_model_environment_is_forwarded(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'synthetic-model-key')
    monkeypatch.setenv('OPENAI_BASE_URL', 'https://example.invalid/v1')
    monkeypatch.setenv('GH_TOKEN', 'synthetic-host-token')
    monkeypatch.setenv('ALICLOUD_ACCESS_KEY_SECRET', 'synthetic-host-cloud-key')
    original_home = module.os.environ.get('HOME')
    env = module.selected_env('/tmp/owned-project', '/tmp/owned-state', 'model', 'server-token')
    assert set(env) == {'OPENAI_API_KEY', 'OPENAI_BASE_URL', 'OPENAI_MODEL', 'ABX_SERVER_TOKEN',
                        'WORKSPACE', 'ABX_SERVER_BASE_DIR', 'ABX_AGENTS_STATE_DIR', 'PATH'}
    assert env['PATH'].startswith('/opt/node/current/bin:')
    assert 'HOME' not in env and module.os.environ.get('HOME') == original_home
    assert 'synthetic-host-token' not in str(env) and 'synthetic-host-cloud-key' not in str(env)


def test_cleanup_exact_nonce_preserves_foreign_sandbox(tmp_path, monkeypatch):
    own = SimpleNamespace(sandbox_id='owned', metadata={'acceptance_run': 'nonce'})
    foreign = SimpleNamespace(sandbox_id='foreign', metadata={'acceptance_run': 'someone-else'})
    class Factory:
        rows = [own, foreign]
        killed = []
        @classmethod
        async def list(cls, **kwargs): return list(cls.rows)
        @classmethod
        async def kill_by_id(cls, identifier, **kwargs):
            cls.killed.append(identifier)
            cls.rows = [r for r in cls.rows if r.sandbox_id != identifier]
    async def no_wait(_): pass
    monkeypatch.setattr(module.asyncio, 'sleep', no_wait)
    report, state = {}, {'nonce': 'nonce'}
    asyncio.run(module.cleanup(Factory, None, state, tmp_path / 'journal.json', report))
    assert Factory.killed == ['owned'] and Factory.rows == [foreign]
    assert all(report['cleanup'].values())
    assert (tmp_path / 'journal.json').stat().st_mode & 0o777 == 0o600


def test_cleanup_readback_permission_error_stops_without_false_absence(tmp_path):
    class Factory:
        calls = 0
        @classmethod
        async def list(cls, **kwargs):
            cls.calls += 1
            raise PermissionError('synthetic403')
    class Sandbox:
        async def kill(self): pass
    report, state = {}, {'nonce': 'nonce', 'sandbox_id': 'owned', 'sandbox_absence_verified': False}
    with pytest.raises(PermissionError):
        asyncio.run(module.cleanup(Factory, Sandbox(), state, tmp_path / 'journal.json', report))
    assert Factory.calls == 1 and report['cleanup']['sandbox_absence_verified'] is False
    assert not state['sandbox_absence_verified']


def test_repeated_listing_page_cannot_claim_absence():
    row = SimpleNamespace(sandbox_id='foreign', metadata={})
    class Factory:
        @classmethod
        async def list(cls, **kwargs): return [row] * 100
    with pytest.raises(AssertionError, match='repeated'):
        asyncio.run(module.owned_rows(Factory, {'nonce': 'owned'}))


def test_http_failure_response_cannot_complete_turn():
    def handle(request):
        if request.method == 'POST' and request.url.path.endswith('/sessions'):
            return httpx.Response(200, headers={'X-Agent-Sandbox-Local': '1'}, json={'id': 'agsess_test'})
        if request.method == 'POST': return httpx.Response(202)
        return httpx.Response(200, json={'status': 'failed', 'error': 'synthetic failure'})
    async def run():
        async with httpx.AsyncClient(base_url='https://example.invalid', transport=httpx.MockTransport(handle)) as client:
            await module.turn(client, '/tmp/owned', 'model', timeout=30)
    with pytest.raises(AssertionError, match='failed'):
        asyncio.run(run())


def test_http_turn_timeout_does_not_report_success(monkeypatch):
    def handle(request):
        if request.url.path.endswith('/sessions'):
            return httpx.Response(200, headers={'X-Agent-Sandbox-Local': '1'}, json={'id': 'agsess_test'})
        return httpx.Response(202)
    times = iter((0, 31))
    # Keep the asyncio loop's real clock; replace only the controller's binding.
    monkeypatch.setattr(module, 'time', SimpleNamespace(monotonic=lambda: next(times)))
    async def run():
        async with httpx.AsyncClient(base_url='https://example.invalid', transport=httpx.MockTransport(handle)) as client:
            await module.turn(client, '/tmp/owned', 'model', timeout=30)
    with pytest.raises(TimeoutError):
        asyncio.run(run())


def test_uncertain_create_recovers_only_its_nonce_and_keeps_failure(tmp_path, monkeypatch):
    foreign = SimpleNamespace(sandbox_id='foreign', metadata={'acceptance_run': 'another-run'})
    class Factory:
        rows, killed = [foreign], []
        @classmethod
        async def create(cls, *args, **kwargs):
            cls.rows.append(SimpleNamespace(sandbox_id='private-owned-id', metadata=kwargs['metadata']))
            raise TimeoutError('synthetic uncertain create')
        @classmethod
        async def list(cls, **kwargs): return list(cls.rows)
        @classmethod
        async def kill_by_id(cls, identifier, **kwargs):
            cls.killed.append(identifier)
            cls.rows = [r for r in cls.rows if r.sandbox_id != identifier]
    async def no_wait(_): pass
    monkeypatch.setattr(module.asyncio, 'sleep', no_wait)
    monkeypatch.setenv('OPENAI_API_KEY', 'synthetic-model-key')
    monkeypatch.setenv('OPENAI_BASE_URL', 'https://example.invalid/v1')
    args = SimpleNamespace(template='synthetic-template', model='model', turn_timeout=30,
                           journal=tmp_path / 'journal.json', report=tmp_path / 'report.json')
    report = asyncio.run(module.run(args, factory=Factory))
    assert report['result'] == 'FAIL' and all(report['cleanup'].values())
    assert Factory.killed == ['private-owned-id'] and Factory.rows == [foreign]
    assert 'private-owned-id' not in args.report.read_text() and 'synthetic-model-key' not in args.journal.read_text()


def test_private_journal_symlink_refused_without_touching_target(tmp_path):
    target = tmp_path / 'valuable'
    target.write_text('preserve')
    journal = tmp_path / 'journal'
    journal.symlink_to(target)
    with pytest.raises(AssertionError): module.save_private(journal, {'nonce': 'test'})
    assert target.read_text() == 'preserve'


def test_run_marks_forbidden_cleanup_intent_and_never_retries(tmp_path, monkeypatch):
    class Factory:
        calls = 0
        @classmethod
        async def create(cls, *args, **kwargs): raise TimeoutError('synthetic uncertain create')
        @classmethod
        async def list(cls, **kwargs):
            cls.calls += 1
            raise PermissionError('synthetic forbidden path')
    monkeypatch.setenv('OPENAI_API_KEY', 'synthetic-model-key')
    monkeypatch.setenv('OPENAI_BASE_URL', 'https://example.invalid/v1')
    args = SimpleNamespace(template='synthetic-template', model='model', turn_timeout=30,
                           journal=tmp_path / 'journal.json', report=tmp_path / 'report.json')
    result = asyncio.run(module.run(args, factory=Factory))
    assert result['result'] == 'FAIL' and result['cleanup']['sandbox_absence_verified'] is False
    assert Factory.calls == 1 and json.loads(args.journal.read_text())['cleanup_permission_denied'] is True


@pytest.mark.parametrize('required', [False, True])
def test_actual_http_suite_keeps_required_model_gate_closed(tmp_path, required):
    # Real SDK HTTP server, explicit synthetic CLI PATH only for this protocol
    # regression. No model/product/cloud success is inferred from this fixture.
    import os
    spec = importlib.util.spec_from_file_location('agents_cli_protocol_fixture', Path(__file__).with_name('test_protocol.py'))
    protocol = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(protocol)
    with protocol.running_server(tmp_path, canonical=True) as (client, token):
        env = {k: v for k, v in os.environ.items() if not any(
            part in k.upper() for part in ('KEY', 'TOKEN', 'SECRET', 'PASSWORD', 'CREDENTIAL'))}
        env.update(E2E_BASE_URL=str(client.base_url).rstrip('/'), E2E_SERVER_TOKEN=token,
                   E2E_RUN_LLM='0', E2E_REQUIRE_LLM='1' if required else '0')
        p = subprocess.run([sys.executable, str(Path(__file__).with_name('e2e_test.py'))],
                           cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30)
        assert p.returncode == int(required)
        if required:
            assert '[FAIL] HTTP-only smoke cannot establish L3' in p.stdout and 'e2e_sdk.py' in p.stdout
        else:
            assert '[SKIP] model/coding acceptance' in p.stdout


@pytest.mark.parametrize('adapter',['qwen-code','codex'])
def test_requested_native_adapter_is_selected_in_actual_session_payload(adapter):
    seen=[]
    def handle(request):
        if request.method=='POST' and request.url.path.endswith('/sessions'):
            seen.append(json.loads(request.content));return httpx.Response(200,headers={'X-Agent-Sandbox-Local':'1'},json={'id':'agsess_selected'})
        if request.method=='POST':return httpx.Response(202)
        if request.url.path.endswith('/items'):return httpx.Response(200,json={'data':[{'type':'message'}]})
        return httpx.Response(200,json={'status':'idle','error':None})
    async def run():
        async with httpx.AsyncClient(base_url='https://example.invalid',transport=httpx.MockTransport(handle)) as client:
            assert await module.turn(client,'/tmp/owned','selected-model',timeout=30,adapter=adapter)=='agsess_selected'
    asyncio.run(run());assert seen[0]['adapter']==adapter and seen[0]['agent']['model']=='selected-model'


def test_unknown_native_adapter_fails_before_http_or_resource_creation():
    async def run():await module.turn(None,'/tmp/owned','model',timeout=30,adapter='unsupported')
    with pytest.raises(AssertionError,match='unsupported native adapter'):asyncio.run(run())
