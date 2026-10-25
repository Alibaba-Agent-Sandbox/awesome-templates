#!/usr/bin/env python3
"""Owned Express native-adapter coding acceptance; independent of the restricted HTTP API.

This controller creates and destroys its own disposable sandbox. Provider-native
commands seed/check files; no general HTTP endpoint is enabled. Never run it in a
shared sandbox. A passing HTTP-only smoke or assistant message is insufficient.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import secrets
import shlex
import tempfile
import textwrap
import time

import httpx

HERE = Path(__file__).resolve().parent
SOURCE = "def fib(n):\n    if n < 0:\n        raise ValueError('negative')\n    return n\n"
ORIGINAL = (
    "import unittest\nfrom fibonacci import fib\n"
    "class OriginalTests(unittest.TestCase):\n"
    "    def test_zero(self): self.assertEqual(fib(0), 0)\n"
    "    def test_seven(self): self.assertEqual(fib(7), 13)\n"
)
ARTIFACT = {"fib7": 13, "fib10": 55}


def require(ok: bool, label: str) -> None:
    if not ok:
        raise AssertionError(label)


def save_private(path: Path, value: dict) -> None:
    """Keep recovery identifiers private, including before a create completes."""
    data = json.dumps(value, indent=2) + "\n"
    require(not path.is_symlink(), 'private journal must not be a symbolic link')
    fd, temporary = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def seed_source(root: str) -> str:
    payload = base64.b64encode(json.dumps({
        "fibonacci.py": SOURCE, "test_original.py": ORIGINAL,
    }).encode()).decode()
    return textwrap.dedent(f"""
        import base64, json, pathlib, subprocess
        root = pathlib.Path({root!r})
        root.mkdir(mode=0o700, parents=False, exist_ok=False)
        for name, text in json.loads(base64.b64decode({payload!r})).items():
            (root / name).write_text(text)
        subprocess.run(['git', 'init', '-q', str(root)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    """)


def verifier_source(root: str, ack: str, *, suites: bool, baseline: bool = False) -> str:
    """Compile source in isolated Python; ACK is minted after the agent finishes.

    This rejects premature exit/skip/pycache success. It is not a security boundary
    against arbitrary hostile same-user code which can inspect its own process.
    """
    prefix = '''
import contextlib, hashlib, io, json, pathlib, sys, types, unittest
ROOT = pathlib.Path(ROOT_LITERAL)
ACK = ACK_LITERAL
def raw(name):
    path = ROOT / name
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1048576:
        raise AssertionError('missing, symbolic, or oversized file')
    return path.read_bytes()
def load_source(name, content):
    module = types.ModuleType(name)
    module.__file__ = str(ROOT / (name + '.py'))
    sys.modules[name] = module
    exec(compile(content, module.__file__, 'exec'), module.__dict__)
    return module
try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        original_bytes = raw('test_original.py')
        if hashlib.sha256(original_bytes).hexdigest() != ORIGINAL_HASH:
            raise AssertionError('original tests changed')
        source_bytes = raw('fibonacci.py')
        if BASELINE:
            if source_bytes != INITIAL_SOURCE:
                raise AssertionError('baseline source changed')
        else:
            if source_bytes == INITIAL_SOURCE:
                raise AssertionError('source unchanged')
            if json.loads(raw('result.json')) != EXPECTED_ARTIFACT or not raw('report.md').strip():
                raise AssertionError('artifact or report missing/incorrect')
        sys.path.insert(0, str(ROOT))
        fibonacci = load_source('fibonacci', source_bytes)
BODY
except BaseException:
    raise SystemExit(1)
print(ACK, flush=True)
'''
    if baseline:
        body = '''
original = load_source('test_original', original_bytes)
suite = unittest.TestLoader().loadTestsFromModule(original)
result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
if (suite.countTestCases() != 2 or result.testsRun != 2 or len(result.failures) != 1
        or result.errors or result.skipped or result.expectedFailures or result.unexpectedSuccesses
        or not result.failures[0][0].id().endswith('.test_seven')):
    raise AssertionError('expected exact broken baseline')
'''
    elif suites:
        body = '''
original = load_source('test_original', original_bytes)
generated = load_source('test_fibonacci', raw('test_fibonacci.py'))
loader = unittest.TestLoader()
original_suite = loader.loadTestsFromModule(original)
generated_suite = loader.loadTestsFromModule(generated)
if original_suite.countTestCases() != 2 or generated_suite.countTestCases() < 1:
    raise AssertionError('test counts')
suite = unittest.TestSuite([original_suite, generated_suite])
result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
if (result.testsRun < 3 or not result.wasSuccessful() or result.skipped
        or result.expectedFailures or result.unexpectedSuccesses):
    raise AssertionError('tests did not all run successfully')
'''
    else:
        body = '''
if [fibonacci.fib(n) for n in (0,1,2,7,10)] != [0,1,1,13,55]:
    raise AssertionError('held-out results')
try:
    fibonacci.fib(-1)
except ValueError:
    pass
else:
    raise AssertionError('negative input')
'''
    return textwrap.dedent(prefix).replace('ROOT_LITERAL', repr(root)).replace(
        'ACK_LITERAL', repr(ack)).replace('ORIGINAL_HASH', repr(hashlib.sha256(ORIGINAL.encode()).hexdigest())
        ).replace('INITIAL_SOURCE', repr(SOURCE.encode())).replace('EXPECTED_ARTIFACT', repr(ARTIFACT)
        ).replace('BASELINE', repr(baseline)).replace(
        'BODY', textwrap.indent(textwrap.dedent(body).strip(), '        '))


async def native(sandbox, code: str, *, timeout: int = 30):
    # -I excludes cwd/user site packages, -S excludes sitecustomize, and -B
    # prevents bytecode writes. Explicit compile(source_bytes) above avoids
    # loading agent-supplied .pyc. Shell quoting preserves literal source bytes.
    return await sandbox.commands.run('python3 -I -S -B -c ' + shlex.quote(code), timeout=timeout)


async def verify(sandbox, root: str, *, suites: bool, baseline: bool = False) -> None:
    ack = secrets.token_hex(32)
    result = await native(sandbox, verifier_source(root, ack, suites=suites, baseline=baseline))
    require(result.exit_code == 0 and result.stdout.strip() == ack,
            'independent baseline' if baseline else 'independent tests/artifact verification')


async def owned_rows(factory, state: dict) -> list:
    rows, offset, seen = [], 0, set()
    for _ in range(100):
        page = await asyncio.wait_for(factory.list(provider='alicloud-express', limit=100, offset=offset), 90)
        require(isinstance(page, list) and len(page) <= 100, 'malformed sandbox listing')
        for row in page:
            require(isinstance(row.sandbox_id, str) and bool(row.sandbox_id)
                    and isinstance(row.metadata, dict), 'malformed sandbox listing row')
            require(row.sandbox_id not in seen, 'repeated sandbox listing page')
            seen.add(row.sandbox_id)
            if row.sandbox_id == state.get('sandbox_id') or row.metadata.get('acceptance_run') == state['nonce']:
                rows.append(row)
        if len(page) < 100:
            return rows
        offset += len(page)
    raise RuntimeError('sandbox listing did not terminate')


async def cleanup(factory, sandbox, state: dict, journal: Path, report: dict) -> None:
    """A failed/uncertain create is recovered only by its unpredictable nonce."""
    report['cleanup'] = {'sandbox_kill': False, 'sandbox_absence_verified': False}
    if sandbox is not None:
        await asyncio.wait_for(sandbox.kill(), 90)
    elif state.get('sandbox_id'):
        await asyncio.wait_for(factory.kill_by_id(state['sandbox_id'], provider='alicloud-express'), 90)
    # Always perform scoped discovery, also after known-ID kill. It covers a
    # create that failed before its response and never deletes foreign resources.
    for attempt in range(3):
        for row in await owned_rows(factory, state):
            await asyncio.wait_for(factory.kill_by_id(row.sandbox_id, provider='alicloud-express'), 90)
        if attempt < 2:
            await asyncio.sleep(2)
    state['sandbox_killed'] = True
    report['cleanup']['sandbox_kill'] = True
    save_private(journal, state)
    require(not await owned_rows(factory, state), 'owned sandbox still listed after kill')
    report['cleanup']['sandbox_absence_verified'] = True
    state['sandbox_absence_verified'] = True
    save_private(journal, state)


async def turn(client: httpx.AsyncClient, root: str, model: str, *, timeout: int, adapter: str = "qwen-code") -> str:
    require(adapter in {"qwen-code", "codex"}, "unsupported native adapter")
    response = await client.post('/v1/agents/sessions', json={
        'adapter': adapter, 'agent': {'model': model},
        'environment': {'type': 'self_hosted', 'workspace_directory': root},
    })
    require(response.status_code == 200 and response.headers.get('X-Agent-Sandbox-Local') == '1',
            f'local {adapter} session creation')
    session = response.json().get('id')
    require(isinstance(session, str) and re.fullmatch(r'[A-Za-z0-9_-]{1,128}', session) is not None,
            'invalid session identifier')
    prompt = (
        'Fix the existing fibonacci.py: fib(n) returns Fibonacci numbers with fib(0)=0, fib(1)=1, '
        'and rejects negative integers with ValueError. Do not change test_original.py. '
        'Create test_fibonacci.py using stdlib unittest with zero, positive and negative cases. '
        'Run both complete unittest modules. Write result.json containing exactly '
        '{"fib7":13,"fib10":55} and a nonempty report.md describing the change and test results. '
        'Actually edit the files in your current workspace; a text response alone is insufficient.'
    )
    response = await client.post(f'/v1/agents/sessions/{session}/events', json={'events': [{
        'type': 'agent.session.input.message',
        'input': [{'role': 'user', 'content': [{'type': 'input_text', 'text': prompt}]}],
    }]})
    require(response.status_code == 202, f'{adapter} turn submission')
    deadline, observed = time.monotonic() + timeout, False
    while time.monotonic() < deadline:
        response = await client.get(f'/v1/agents/sessions/{session}')
        require(response.status_code == 200, f'{adapter} session reconnect')
        state = response.json()
        require(state.get('error') is None and state.get('status') != 'failed', f'{adapter} model turn failed')
        response = await client.get(f'/v1/agents/sessions/{session}/items', params={'limit': 100, 'order': 'asc'})
        require(response.status_code == 200 and isinstance(response.json().get('data'), list), f'{adapter} items polling')
        observed = observed or bool(response.json()['data'])
        if state.get('status') == 'idle' and observed:
            return session
        await asyncio.sleep(1)
    raise TimeoutError(adapter+' turn deadline; destroy the owned sandbox to cancel')


def completed_source(state_dir: str, session: str, ack: str) -> str:
    # The restricted public session view exposes idle, not the last turn's exit
    # status. Read the ORIGINAL server's own persisted state out of band; never
    # accept a caller-provided receipt. Files/tests remain independent checks.
    return textwrap.dedent(f'''
        import json, pathlib
        path = pathlib.Path({state_dir!r}) / 'sessions.json'
        assert not path.is_symlink() and path.stat().st_size < 8388608
        sessions = json.loads(path.read_bytes())['sessions']
        rows = [s for s in sessions if s.get('id') == {session!r}]
        assert len(rows) == 1 and len(rows[0]['turns']) == 1
        turn = rows[0]['turns'][0]
        assert turn['status'] == 'completed' and not turn.get('error')
        print({ack!r})
    ''')


def codex_profile_source(home: str, base_url: str) -> str:
    """An explicit native HTTP Responses provider; no credential is written."""
    text=('model_provider = "owned_compatible"\n'
          '[model_providers.owned_compatible]\n'
          'name = "Owned compatible endpoint"\n'
          'base_url = '+json.dumps(base_url)+'\n'
          'env_key = "OPENAI_API_KEY"\n'
          'wire_api = "responses"\n'
          'supports_websockets = false\n')
    return ("from pathlib import Path\nimport os\nroot=Path("+repr(home)+")\n"
            "root.mkdir(mode=0o700,parents=True,exist_ok=False)\n"
            "path=root/'config.toml'\npath.write_text("+repr(text)+")\npath.chmod(0o600)\nprint('PROFILE_OK')\n")


def selected_env(root: str, state_dir: str, model: str, token: str, *, adapter: str = "qwen-code") -> dict[str, str]:
    env = {name: os.environ[name] for name in ('OPENAI_API_KEY', 'OPENAI_BASE_URL')}
    env.update(PATH="/opt/node/current/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin",
               OPENAI_MODEL=model, ABX_SERVER_TOKEN=token, WORKSPACE=root,
               ABX_SERVER_BASE_DIR=root, ABX_AGENTS_STATE_DIR=state_dir)
    if adapter == "codex":env["CODEX_HOME"]=state_dir+"/codex-home"
    return env


async def run(args, *, factory=None) -> dict:
    if factory is None:
        from agent_sandbox import ProviderSandbox
        factory = Sandbox
    adapter=getattr(args, 'adapter', 'qwen-code')
    require(adapter in {'qwen-code','codex'}, 'unsupported native adapter')
    require(args.template and args.model and 30 <= args.turn_timeout <= 600, 'invalid template/model/timeout')
    require(all(os.environ.get(name) for name in ('OPENAI_API_KEY', 'OPENAI_BASE_URL')), 'compatible model configuration missing')
    require(not args.journal.exists(), 'journal exists; resolve its owned resources before a new run')
    require(args.journal.resolve() != args.report.resolve(), 'journal and public report must differ')
    state = {'nonce': secrets.token_hex(16), 'sandbox_create_attempted': False,
             'sandbox_killed': False, 'sandbox_absence_verified': False}
    # Reserve the caller's new intent path exclusively before a create can run.
    descriptor = os.open(args.journal, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    os.close(descriptor)
    save_private(args.journal, state)
    report = {'result': 'FAIL', 'adapter': adapter, 'provider': 'alicloud-express',
              'model': args.model, 'checks': [], 'cleanup': {},
              'boundary': 'real owned-template SDK/session coding acceptance for the selected native adapter; not hosted Agents or a build-mode claim'}
    sandbox = reader = drain = None
    attempted = False
    try:
        state['sandbox_create_attempted'] = attempted = True
        save_private(args.journal, state)
        sandbox = await factory.create(args.template, provider='alicloud-express', timeout=1800,
            request_timeout=120, metadata={'acceptance_run': state['nonce'], 'purpose': 'agents-cli-'+adapter+'-l3'})
        state['sandbox_id'] = sandbox.id
        save_private(args.journal, state)
        expected = {n: hashlib.sha256((HERE / n).read_bytes()).hexdigest() for n in ('commands.py', 'server-policy.json')}
        code = ("import hashlib,json,pathlib;root=pathlib.Path('/home/user/app');print(json.dumps({n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in " + repr(list(expected)) + "}))")
        provenance = await native(sandbox, code)
        require(provenance.exit_code == 0 and json.loads(provenance.stdout) == expected, 'actual image runtime provenance')
        report['runtime_file_sha256'] = expected
        root = '/tmp/agents-cli-l3-' + state['nonce']
        seeded = await native(sandbox, seed_source(root))
        require(seeded.exit_code == 0, 'native project seed')
        await verify(sandbox, root, suites=True, baseline=True)
        report['checks'].append('exact original baseline: test_seven FAIL, test_zero PASS')
        token = secrets.token_hex(32)
        # No host/cloud/GitHub credentials, HOME override, or source overlay.
        state_dir = '/tmp/agents-cli-state-' + state['nonce']
        selected = selected_env(root, state_dir, args.model, token, adapter=adapter)
        if adapter == "codex":
            configured=await native(sandbox,codex_profile_source(selected["CODEX_HOME"],selected["OPENAI_BASE_URL"]))
            require(configured.exit_code==0 and configured.stdout.strip()=="PROFILE_OK", "private native Codex provider configuration")
            report["checks"].append("private explicit native HTTP Responses provider; websockets disabled; no key file")
        reader = await sandbox.commands.start(
            'agent-sandbox-server serve --port 9010 --commands /home/user/app/commands.py '
            '--policy /home/user/app/server-policy.json', env=selected, timeout=1500)
        started, errors = asyncio.Event(), []
        async def consume():
            try:
                async for chunk in reader:
                    if chunk.pid:
                        state['server_pid'] = chunk.pid
                        save_private(args.journal, state)
                        started.set()
            except Exception as exc:
                errors.append(type(exc).__name__)
                started.set()
        drain = asyncio.create_task(consume())
        await asyncio.wait_for(started.wait(), 120)
        require(not errors, 'configured server start')
        url, headers = await sandbox.network.resolve(9010)
        headers = dict(headers)
        headers['Authorization'] = 'Bearer ' + token
        async with httpx.AsyncClient(base_url=url, headers=headers, timeout=30) as client:
            for _ in range(40):
                try:
                    response = await client.get('/health', timeout=5)
                    if response.status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                await asyncio.sleep(1)
            else:
                raise RuntimeError('configured server readiness')
            response = await client.post('/commands/agents_version', json={})
            require(response.status_code == 200 and response.json().get('result') ==
                    'codex 0.162.1; qwen-code 0.23.0', 'actual pinned CLI versions')
            for method, path in (('POST', '/shell'), ('GET', '/files'), ('POST', '/process/start')):
                response = await client.request(method, path, json={} if method == 'POST' else None)
                require(response.status_code == 404, 'restricted policy retained')
            report['checks'].append('new9010 configured, actual pinned CLIs, original restricted HTTP policy')
            session = await turn(client, root, args.model, timeout=args.turn_timeout, adapter=adapter)
        # Persistence follows the final turn event; allow that bounded write to
        # finish before inspecting it through the separate management channel.
        for attempt in range(10):
            ack = secrets.token_hex(32)
            completed = await native(sandbox, completed_source(state_dir, session, ack), timeout=10)
            if completed.exit_code == 0 and completed.stdout.strip() == ack:
                break
            if attempt == 9:
                raise AssertionError('original server did not persist a completed model turn')
            await asyncio.sleep(.5)
        report['checks'].append('actual '+adapter+' HTTP session/events/reconnect/items turn')
        await verify(sandbox, root, suites=True)
        report['checks'].append('changed existing source, unchanged original tests, exact artifact/report, complete original and generated unittest modules')
        await verify(sandbox, root, suites=False)
        report['checks'].append('six independent held-out cases, source compilation, post-agent random ACK')
        report['result'] = 'PASS'
    except Exception as exc:
        report['failure_category'] = type(exc).__name__
    finally:
        if attempted:
            try:
                await cleanup(factory, sandbox, state, args.journal, report)
            except BaseException as exc:
                report['result'] = 'FAIL'
                report['cleanup_error_category'] = type(exc).__name__
                # One permission error ends this path. Keep recovery intent.
                if (isinstance(exc, PermissionError)
                        or getattr(getattr(exc, 'response', None), 'status_code', None) == 403
                        or re.search(r'\b403\b', str(exc))):
                    state['cleanup_permission_denied'] = True
                save_private(args.journal, state)
        if drain is not None:
            drain.cancel()
            await asyncio.gather(drain, return_exceptions=True)
        if reader is not None:
            try:
                await asyncio.wait_for(reader.cancel(), 10)
            except Exception as exc:
                report['result'] = 'FAIL'
                report['stream_close_error_category'] = type(exc).__name__
        # Identifiers remain in the private journal; public evidence is sanitized.
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--template', required=True, help='private owned agents-cli template ID')
    parser.add_argument('--adapter', choices=('qwen-code','codex'), default='qwen-code', help='exact native CLI adapter; each run owns a new sandbox')
    parser.add_argument('--model', default=os.environ.get('OPENAI_MODEL', 'qwen3.8-flash'))
    parser.add_argument('--turn-timeout', type=int, default=540)
    parser.add_argument('--journal', type=Path, required=True, help='new private recovery file; retain on failure')
    parser.add_argument('--report', type=Path, required=True, help='sanitized result, no raw model output')
    args = parser.parse_args()
    logging.disable(logging.CRITICAL)
    try:
        report = asyncio.run(run(args))
    except BaseException as exc:
        print('[FAIL] SDK verifier (' + type(exc).__name__ + '); private details omitted', flush=True)
        return 1
    print('[' + report['result'] + '] owned '+report['adapter']+' SDK coding verifier; cleanup recorded', flush=True)
    return 0 if report['result'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
