"""Verify patched command source on Express; this does not build its Dockerfile.

All credentials stay in memory/process environments. Only owned sandbox resources
are destroyed. This diagnostic writes no template provider-acceptance evidence.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.metadata
import hashlib
import json
import logging
import os
from pathlib import Path
import secrets
import shlex
import sys
from datetime import datetime, timezone

import httpx
from agent_sandbox import Sandbox

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('template', choices=['codex', 'codex-agent-api', 'python-hello'])
parser.add_argument('--server-wheel', type=Path, required=True)
parser.add_argument('--output-dir', type=Path, required=True)
parser.add_argument('--base-template', default='base')
parser.add_argument('--model', default='')
parser.add_argument('--sdk-source-commit', default='not recorded')
ARGS = parser.parse_args()
IS_CODEX = ARGS.template in {'codex', 'codex-agent-api'}
if IS_CODEX and not ARGS.model:
    parser.error('--model is required for Codex templates')
if not ARGS.server_wheel.is_file():
    parser.error('--server-wheel must point to a built agent-sandbox-server wheel')
if IS_CODEX and not all(os.environ.get(name) for name in ('OPENAI_API_KEY', 'OPENAI_BASE_URL')):
    parser.error('Codex templates require OPENAI_API_KEY and OPENAI_BASE_URL in the environment')
TEMPLATE = ARGS.template
OUT = ARGS.output_dir.resolve()
OUT.mkdir(parents=True, exist_ok=True)
VALUES = dict(os.environ)
SERVER_TOKEN = secrets.token_urlsafe(32)
logging.disable(logging.CRITICAL)
os.environ['ABX_ENGINE_SOCKET'] = f'/tmp/abx-runtime-{os.getpid()}.sock'
os.environ['ABX_ENGINE_INPROCESS'] = '1'


def scrub(value: str) -> str:
    for name, secret in VALUES.items():
        if secret and any(word in name.upper() for word in ('KEY', 'TOKEN', 'SECRET', 'PASSWORD')):
            value = value.replace(secret, '[REDACTED]')
    return value.replace(SERVER_TOKEN, '[REDACTED]')


async def main() -> int:
    sb = None
    child = None
    report = {
        'date': datetime.now(timezone.utc).isoformat(),
        'provider': 'alicloud-express', 'template': TEMPLATE,
        'scope': 'patched-source runtime on existing base; NOT Dockerfile L1 or template-deploy L2',
        'source_sha256': hashlib.sha256((ROOT / TEMPLATE / 'commands.py').read_bytes()).hexdigest(),
        'server_wheel_sha256': hashlib.sha256(ARGS.server_wheel.read_bytes()).hexdigest(),
        'sdk_version': importlib.metadata.version('agent-sandbox-client'),
        'sdk_source_commit': ARGS.sdk_source_commit,
        'base_template': ARGS.base_template,
        'verification_type': 'source-runtime',
        'image_build_verified': False, 'template_deploy_verified': False,
        'checks': [],
    }

    def record(name: str, ok: bool, detail: str = '') -> None:
        row = {'name': name, 'ok': ok}
        if detail:
            row['detail'] = scrub(detail)
        report['checks'].append(row)
        print(f'{name}: {"PASS" if ok else "FAIL"}' + (f' {scrub(detail)}' if detail else ''), flush=True)

    try:
        sb = await Sandbox.create(template=ARGS.base_template, timeout=900, request_timeout=45,
                                  metadata={'purpose': 'agent-sandbox-e2e', 'run': 'source-runtime-' + TEMPLATE + '-' + secrets.token_hex(6)})
        record('owned Express base sandbox', True)
        remote = '/home/user/abx-' + TEMPLATE + '-runtime'
        made = await sb.commands.run(f'mkdir -p {remote}/workspace {remote}/codex-home', timeout=30)
        if made.exit_code != 0:
            raise RuntimeError('could not prepare runtime workspace')
        wheel = ARGS.server_wheel.resolve()
        await sb.files.write(remote + '/' + wheel.name, wheel.read_bytes())
        await sb.files.write(remote + '/commands.py', (ROOT / TEMPLATE / 'commands.py').read_text())
        install = (
            f'python3 -m pip install --no-cache-dir --target {remote}/site {remote}/{wheel.name} '
        )
        if IS_CODEX:
            install += (f' && npm install --prefix {remote}/tools --registry=https://registry.npmjs.org '
                        '--ignore-scripts --no-audit --no-fund @openai/codex@0.162.1')
        else:
            install += ' pytest==8.4.2'
        installed = await sb.commands.run(install, timeout=240, shell=True)
        (OUT / (TEMPLATE + '-runtime-install.log')).write_text(scrub(installed.stdout + '\n' + installed.stderr))
        record('pinned runtime dependency install', installed.exit_code == 0)
        if installed.exit_code != 0:
            raise RuntimeError('runtime install failed; see sanitized installation log')
        env = {
            'PYTHONPATH': remote + '/site',
            'PATH': remote + '/tools/node_modules/.bin:/usr/local/bin:/usr/bin:/bin',
            'WORKSPACE': remote + '/workspace', 'CODEX_HOME': remote + '/codex-home',
            'ABX_SERVER_BASE_DIR': remote, 'ABX_SERVER_PORT': '9000',
            'ABX_PTY_PORT': '9001', 'ABX_SERVER_TOKEN': SERVER_TOKEN,
        }
        if IS_CODEX:
            env.update({'OPENAI_API_KEY': VALUES['OPENAI_API_KEY'],
                        'OPENAI_BASE_URL': VALUES['OPENAI_BASE_URL'], 'CODEX_MODEL': ARGS.model})
        serve = (f'python3 -m agent_sandbox.server serve --port 9000 --commands {remote}/commands.py'
                 if TEMPLATE == 'codex-agent-api' else f'python3 {remote}/commands.py')
        start = f'nohup {serve} </dev/null >{remote}/server.log 2>&1 &'
        result = await sb.commands.run('sh -c ' + shlex.quote(start), env=env, timeout=15)
        record('patched server process start', result.exit_code == 0)
        async with sb.server_at(token=SERVER_TOKEN, timeout=30) as server:
            healthy = False
            async with httpx.AsyncClient(timeout=15) as health_client:
                for _ in range(15):
                    response = await health_client.get(sb.network.get_url(9000) + '/health')
                    if response.status_code == 501:
                        raise RuntimeError('HTTP 501: ' + response.text[:500])
                    if response.status_code not in {200, 502, 503}:
                        raise RuntimeError('health endpoint returned HTTP ' + str(response.status_code))
                    healthy = response.status_code == 200 and response.json().get('status') == 'ok'
                    if healthy:
                        break
                    await asyncio.sleep(1)
            record('external SDK health', healthy)
            if not healthy:
                raise RuntimeError('patched runtime server did not become healthy')
            if IS_CODEX:
                version = await server.commands.run('codex_version')
                record('pinned Codex version through SDK', version == '0.162.1', str(version))
            else:
                result = await server.commands.run('hello', name='Express')
                record('named hello through SDK', result == 'Hello, Express!')
                version = await sb.commands.run('python3 -m pytest --version', env=env, timeout=15)
                record('pinned pytest version', version.exit_code == 0 and version.stdout.strip() == 'pytest 8.4.2')

        # The HTTP verifier needs no GitHub or cloud control-plane credentials.
        keep = {'PATH', 'HOME', 'LANG', 'LC_ALL', 'SSL_CERT_FILE', 'SSL_CERT_DIR',
                'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY',
                'http_proxy', 'https_proxy', 'all_proxy', 'no_proxy'}
        child_env = {key: value for key, value in os.environ.items() if key in keep}
        if IS_CODEX:
            child_env['OPENAI_API_KEY'] = VALUES['OPENAI_API_KEY']
        child_env.update({
            'E2E_BASE_URL': sb.network.get_url(9000), 'E2E_TOKEN': SERVER_TOKEN,
            'E2E_WORKSPACE': remote + '/workspace', 'E2E_MODEL': ARGS.model,
            'E2E_RUN_LLM': '1' if IS_CODEX else '0',
            'E2E_REQUIRE_LLM': '1' if IS_CODEX else '0', 'E2E_LLM_TIMEOUT': '420',
        })
        child = await asyncio.create_subprocess_exec(
            sys.executable, str(ROOT / TEMPLATE / 'e2e_test.py'),
            env=child_env, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
        )
        output, _ = await asyncio.wait_for(child.communicate(), 540)
        text = scrub(output.decode(errors='replace')).replace(sb.id, '[OWNED_SANDBOX]')
        (OUT / (TEMPLATE + '-express-runtime.log')).write_text(text)
        record('remote HTTP suite' + (' with real model required' if IS_CODEX else ''), child.returncode == 0,
               f'exit={child.returncode}; PASS lines={text.count("[PASS]")}; FAIL lines={text.count("[FAIL]")}')
    except Exception as exc:
        record('runtime exception', False, type(exc).__name__ + ': ' + str(exc)[:800])
    finally:
        if child is not None and child.returncode is None:
            child.kill()
            await child.wait()
        if sb is not None:
            try:
                await asyncio.wait_for(sb.kill(), 30)
                record('owned sandbox cleanup', True)
            except Exception as exc:
                record('owned sandbox cleanup', False, type(exc).__name__)
        report['passed'] = bool(report['checks']) and all(row['ok'] for row in report['checks'])
        (OUT / (TEMPLATE + '-express-runtime.json')).write_text(scrub(json.dumps(report, indent=2)) + '\n')
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))
