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
from agent_sandbox import ProviderSandbox

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('template', choices=['codex', 'codex-agent-api', 'python-hello',
                                         'opencode', 'browser-automation', 'node-web', 'amp', 'droid', 'qwen-code', 'gemini'])
parser.add_argument('--server-wheel', type=Path, required=True)
parser.add_argument('--output-dir', type=Path, required=True)
parser.add_argument('--base-template', default='base')
parser.add_argument('--model', default='', help='Required for model templates; OpenCode uses dashscope/<model>')
parser.add_argument('--sdk-source-commit', default='not recorded')
ARGS = parser.parse_args()
IS_CODEX = ARGS.template in {'codex', 'codex-agent-api'}
IS_OPENCODE = ARGS.template == 'opencode'
IS_QWEN = ARGS.template == 'qwen-code'
MODEL_REQUIRED = IS_CODEX or IS_OPENCODE or IS_QWEN
if MODEL_REQUIRED and not ARGS.model.strip():
    parser.error('--model is required for coding-agent model templates')
if IS_OPENCODE:
    if '/' not in ARGS.model:
        ARGS.model = 'dashscope/' + ARGS.model
    if not ARGS.model.startswith('dashscope/') or not ARGS.model.removeprefix('dashscope/').strip():
        parser.error('OpenCode uses the configured dashscope/<model> provider alias')
if not ARGS.server_wheel.is_file():
    parser.error('--server-wheel must point to a built agent-sandbox-server wheel')
if IS_CODEX and not all(os.environ.get(name) for name in ('OPENAI_API_KEY', 'OPENAI_BASE_URL')):
    parser.error('Codex templates require OPENAI_API_KEY and OPENAI_BASE_URL in the environment')
if IS_OPENCODE and not all(os.environ.get(name) for name in ('ABX_LLM_API_KEY', 'ABX_LLM_BASE_URL')):
    parser.error('OpenCode requires ABX_LLM_API_KEY and ABX_LLM_BASE_URL in the environment')
if IS_QWEN and not all(os.environ.get(name) for name in ('OPENAI_API_KEY', 'OPENAI_BASE_URL')):
    parser.error('Qwen Code requires OPENAI_API_KEY and OPENAI_BASE_URL in the environment')
TEMPLATE = ARGS.template
OUT = ARGS.output_dir.resolve()
OUT.mkdir(parents=True, exist_ok=True)
VALUES = dict(os.environ)
SERVER_TOKEN = secrets.token_urlsafe(32)
logging.disable(logging.CRITICAL)
# Concurrent native execs can expose the same PID while sharing the filesystem.
# A run nonce prevents attaching to another process's short-lived engine.
os.environ['ABX_ENGINE_SOCKET'] = f'/tmp/abx-runtime-{os.getpid()}-{secrets.token_hex(6)}.sock'
os.environ['ABX_ENGINE_INPROCESS'] = '1'


def scrub(value: str) -> str:
    for name, secret in VALUES.items():
        if secret and any(word in name.upper() for word in ('KEY', 'TOKEN', 'SECRET', 'PASSWORD', 'CREDENTIAL')):
            value = value.replace(secret, '[REDACTED]')
    return value.replace(SERVER_TOKEN, '[REDACTED]')


def runtime_files() -> dict[str, bytes]:
    """Public source/config payloads only; credentials never enter upload files."""
    files = {'commands.py': (ROOT / TEMPLATE / 'commands.py').read_bytes()}
    if IS_OPENCODE:
        files['opencode.json'] = (ROOT / TEMPLATE / 'opencode.json').read_bytes()
    elif TEMPLATE == 'amp':
        files['settings.json'] = (ROOT / TEMPLATE / 'settings.json').read_bytes()
    elif TEMPLATE == 'node-web':
        index = (ROOT / TEMPLATE / 'index.js').read_bytes()
        files.update({'index.js': index, 'workspace/index.js': index})
        # The image is dependency-free and has no package.json. This public
        # fixture makes its npm command entry points usable in the runtime.
        files['workspace/package.json'] = (json.dumps({
            'private': True, 'scripts': {'start': 'node index.js', 'dev': 'node index.js',
                                        'build': 'node --check index.js'},
        }, indent=2) + '\n').encode()
    return files


async def background_install(sb: Sandbox, install: str, remote: str) -> tuple[int, str]:
    """Poll an owned install job using short RPCs, instead of one long stream."""
    status = remote + '/install.exit'
    job = (install + '; code=$?; printf "%s" "$code" >' + status + '.tmp; '
           'mv ' + status + '.tmp ' + status)
    launch = ('nohup sh -c ' + shlex.quote(job) + ' </dev/null >' + remote + '/install.log 2>&1 &')
    started = await sb.commands.run('sh -c ' + shlex.quote(launch), timeout=15)
    if started.exit_code != 0:
        raise RuntimeError('could not start owned dependency installation')
    loop = asyncio.get_running_loop()
    deadline = loop.time() + 300
    last_notice = loop.time()
    while loop.time() < deadline:
        result = await sb.commands.run(
            'if test -f ' + status + '; then cat ' + status + '; else printf RUNNING; fi',
            timeout=15, shell=True,
        )
        value = result.stdout.strip()
        if result.exit_code != 0:
            raise RuntimeError('could not inspect owned dependency installation')
        if value.isdecimal():
            return int(value), await sb.files.read(remote + '/install.log')
        if value != 'RUNNING':
            raise RuntimeError('invalid owned installation status')
        if loop.time() - last_notice >= 20:
            print('owned dependency installation: RUNNING', flush=True)
            last_notice = loop.time()
        await asyncio.sleep(2)
    raise RuntimeError('owned dependency installation exceeded 300 seconds; sandbox cleanup will stop it')


async def main() -> int:
    sb = None
    child = None
    files = runtime_files()
    source_paths = [ROOT / TEMPLATE / name for name in ('commands.py', 'e2e_test.py', 'Dockerfile', 'template.yaml')]
    source_paths.append(Path(__file__).resolve())
    source_paths.extend(ROOT / TEMPLATE / name for name in ('opencode.json', 'index.js', 'settings.json')
                        if (ROOT / TEMPLATE / name).is_file())
    report = {
        'date': datetime.now(timezone.utc).isoformat(),
        'provider': 'alicloud-express', 'template': TEMPLATE,
        'scope': 'patched-source runtime on existing base; NOT Dockerfile L1 or template-deploy L2',
        'source_sha256': hashlib.sha256((ROOT / TEMPLATE / 'commands.py').read_bytes()).hexdigest(),
        'source_files_sha256': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in source_paths},
        'uploaded_files_sha256': {name: hashlib.sha256(content).hexdigest() for name, content in files.items()},
        'generated_fixtures': ['workspace/package.json'] if TEMPLATE == 'node-web' else [],
        'required_model_acceptance': MODEL_REQUIRED,
        'runtime_dependencies': {
            'codex': '@openai/codex@0.162.1', 'codex-agent-api': '@openai/codex@0.162.1',
            'python-hello': 'pytest==8.4.2', 'opencode': 'opencode-ai@1.19.0',
            'browser-automation': 'playwright==1.58.0 and its pinned Chromium; system libraries supplied by base image',
            'node-web': 'base-image Node.js 20; dependency-free public sample',
            'amp': '@ampcode/cli@0.0.1792022479-ge66e24; keyless inspection only',
            'droid': '@factory/cli@0.241.1; keyless inspection only',
            'qwen-code': '@qwen-code/qwen-code@0.23.0',
            'gemini': '@google/gemini-cli@0.64.0; keyless inspection only',
        }[TEMPLATE],
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
        sb = await ProviderSandbox.create(template=ARGS.base_template, timeout=900, request_timeout=45,
                                  cpu=2, memory=4096 if TEMPLATE in {'qwen-code', 'gemini'} else 2048,
                                  metadata={'purpose': 'agent-sandbox-e2e', 'run': 'source-runtime-' + TEMPLATE + '-' + secrets.token_hex(6)})
        record('owned Express base sandbox', True)
        remote = '/home/user/abx-' + TEMPLATE + '-runtime'
        made = await sb.commands.run(f'mkdir -p {remote}/workspace {remote}/codex-home', timeout=30)
        if made.exit_code != 0:
            raise RuntimeError('could not prepare runtime workspace')
        wheel = ARGS.server_wheel.resolve()
        await sb.files.write(remote + '/' + wheel.name, wheel.read_bytes())
        for relative, content in files.items():
            await sb.files.write(remote + '/' + relative, content)
        record('public runtime source and config upload', True)
        install = (
            f'python3 -m pip install --no-cache-dir --target {remote}/site {shlex.quote(remote + "/" + wheel.name)} '
        )
        if IS_CODEX:
            install += (f' && npm install --prefix {remote}/tools --registry=https://registry.npmjs.org '
                        '--ignore-scripts --no-audit --no-fund @openai/codex@0.162.1')
        elif IS_OPENCODE:
            install += (f' && npm install --prefix {remote}/tools --registry=https://registry.npmjs.org '
                        '--no-audit --no-fund opencode-ai@1.19.0')
        elif TEMPLATE == 'browser-automation':
            install += (f' playwright==1.58.0 && PYTHONPATH={remote}/site '
                        f'PLAYWRIGHT_BROWSERS_PATH={remote}/playwright python3 -m playwright install chromium')
        elif TEMPLATE == 'python-hello':
            install += ' pytest==8.4.2'
        elif TEMPLATE == 'amp':
            install += (f' && npm install --prefix {remote}/tools --registry=https://registry.npmjs.org '
                        '--no-audit --no-fund @ampcode/cli@0.0.1792022479-ge66e24')
        elif TEMPLATE == 'droid':
            install += (f' && npm install --prefix {remote}/tools --registry=https://registry.npmjs.org '
                        '--no-audit --no-fund @factory/cli@0.241.1')
        elif IS_QWEN:
            install += (f' && npm install --prefix {remote}/tools --registry=https://registry.npmjs.org '
                        '--no-audit --no-fund @qwen-code/qwen-code@0.23.0')
        elif TEMPLATE == 'gemini':
            install += (f' && npm install --prefix {remote}/tools --registry=https://registry.npmjs.org '
                        '--no-audit --no-fund @google/gemini-cli@0.64.0')
        if TEMPLATE in {'amp', 'droid', 'qwen-code', 'gemini'}:
            install_code, install_log = await background_install(sb, install, remote)
        else:
            installed = await sb.commands.run(install, timeout=240, shell=True)
            install_code, install_log = installed.exit_code, installed.stdout + '\n' + installed.stderr
        (OUT / (TEMPLATE + '-runtime-install.log')).write_text(scrub(install_log))
        record('pinned runtime dependency install', install_code == 0)
        if install_code != 0:
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
        elif IS_OPENCODE:
            env.update({'ABX_LLM_API_KEY': VALUES['ABX_LLM_API_KEY'],
                        'ABX_LLM_BASE_URL': VALUES['ABX_LLM_BASE_URL'], 'OPENCODE_MODEL': ARGS.model,
                        'OPENCODE_CONFIG': remote + '/opencode.json', 'OPENCODE_DISABLE_AUTOUPDATE': 'true'})
        elif TEMPLATE == 'browser-automation':
            env['PLAYWRIGHT_BROWSERS_PATH'] = remote + '/playwright'
        elif TEMPLATE == 'node-web':
            env.update({'NODE_ENV': 'production', 'PORT': '3000'})
        elif TEMPLATE == 'amp':
            env['AMP_SETTINGS_FILE'] = remote + '/settings.json'
        elif TEMPLATE == 'droid':
            env['FACTORY_DROID_AUTO_UPDATE_ENABLED'] = 'false'
        elif IS_QWEN:
            env.update({'OPENAI_API_KEY': VALUES['OPENAI_API_KEY'],
                        'OPENAI_BASE_URL': VALUES['OPENAI_BASE_URL'], 'OPENAI_MODEL': ARGS.model})

        if TEMPLATE == 'browser-automation':
            # Do not run --with-deps here: it would try sudo on non-root Express.
            # Missing shared libraries are a real runtime failure, not a reason
            # to change sandbox flags or claim the Dockerfile apt layer passed.
            probe_code = ("from playwright.sync_api import sync_playwright\n"
                          "with sync_playwright() as runtime:\n"
                          "    browser = runtime.chromium.launch(headless=True, args=['--disable-dev-shm-usage'])\n"
                          "    browser.close()\nprint('CHROMIUM_LAUNCH_OK')\n")
            probe = await sb.commands.run('python3 -c ' + shlex.quote(probe_code), env=env, timeout=45)
            (OUT / (TEMPLATE + '-chromium-launch.log')).write_text(scrub(probe.stdout + '\n' + probe.stderr))
            record('real pinned Chromium launch using base system libraries',
                   probe.exit_code == 0 and probe.stdout.strip() == 'CHROMIUM_LAUNCH_OK')
            if probe.exit_code != 0:
                raise RuntimeError('Chromium launch failed; inspect sanitized browser diagnostics for missing system libraries or runtime restrictions')
        serve = (f'python3 -m agent_sandbox.server serve --port 9000 --commands {remote}/commands.py'
                 if TEMPLATE == 'codex-agent-api' else f'python3 {remote}/commands.py')
        start = f'nohup {serve} </dev/null >{remote}/server.log 2>&1 &'
        result = await sb.commands.run('sh -c ' + shlex.quote(start), env=env, timeout=15)
        record('patched server process start', result.exit_code == 0)
        async with sb.server_at(token=SERVER_TOKEN, timeout=30) as server:
            healthy = False
            async with httpx.AsyncClient(timeout=15) as health_client:
                for _ in range(15):
                    response = await health_client.get(sb.network.get_url(9000) + '/health',
                                                       headers={'Authorization': 'Bearer ' + SERVER_TOKEN})
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
            elif TEMPLATE == 'python-hello':
                result = await server.commands.run('hello', name='Express')
                record('named hello through SDK', result == 'Hello, Express!')
                version = await sb.commands.run('python3 -m pytest --version', env=env, timeout=15)
                record('pinned pytest version', version.exit_code == 0 and version.stdout.strip() == 'pytest 8.4.2')
            elif IS_OPENCODE:
                version = await server.commands.run('opencode_version')
                record('pinned OpenCode version through SDK', version == '1.19.0', str(version))
                result = await server.commands.run('opencode_setup_check')
                record('OpenCode public configuration smoke', result == 'ok')
            elif TEMPLATE == 'browser-automation':
                result = await server.commands.run('browse', url='data:text/html,<title>ABX_E2E_OK</title><h1>ABX_E2E_OK</h1>', action='extract')
                record('real Chromium smoke through SDK', isinstance(result, dict)
                       and result.get('title') == 'ABX_E2E_OK' and result.get('text') == 'ABX_E2E_OK')
            elif TEMPLATE == 'node-web':
                version = await sb.commands.run('node --version', env=env, timeout=15)
                record('base Node.js 20 runtime', version.exit_code == 0 and version.stdout.strip().startswith('v20.'))
                result = await server.commands.run('smoke')
                record('real bundled Node HTTP smoke through SDK', result == 'node-web ready')
            elif TEMPLATE == 'amp':
                original = files['settings.json']
                version = await server.commands.run('amp_version')
                record('pinned Amp version through SDK', version == '0.0.1792022479-ge66e24')
                setup = await server.commands.run('amp_setup_check')
                record('Amp keyless read-only configuration smoke', isinstance(setup, dict)
                       and setup.get('installed') is True and setup.get('api_key_set') is False
                       and setup.get('settings_exists') is True
                       and setup.get('dangerously_allow_all') is False
                       and setup.get('updates_mode') == 'disabled')
                unchanged = await sb.files.read_bytes(remote + '/settings.json')
                record('Amp version and setup preserve settings bytes', unchanged == original)
            elif TEMPLATE in {'droid', 'qwen-code', 'gemini'}:
                prefix = 'qwen' if IS_QWEN else TEMPLATE
                version = await server.commands.run(prefix + '_version')
                expected_version = {'qwen-code': '0.23.0', 'droid': '0.241.1', 'gemini': '0.64.0'}[TEMPLATE]
                record('pinned ' + prefix + ' version through SDK', version == expected_version)
                setup = await server.commands.run(prefix + '_setup_check')
                record(prefix + ' read-only installation smoke', isinstance(setup, dict)
                       and setup.get('installed') is True and setup.get('api_key_set') is IS_QWEN)

        # The HTTP verifier needs no GitHub or cloud control-plane credentials.
        keep = {'PATH', 'HOME', 'LANG', 'LC_ALL', 'SSL_CERT_FILE', 'SSL_CERT_DIR',
                'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY',
                'http_proxy', 'https_proxy', 'all_proxy', 'no_proxy'}
        child_env = {key: value for key, value in os.environ.items() if key in keep}
        if IS_CODEX:
            child_env['OPENAI_API_KEY'] = VALUES['OPENAI_API_KEY']
        child_env.update({
            'E2E_BASE_URL': sb.network.get_url(9000),
            'ABX_SERVER_TOKEN': SERVER_TOKEN,
            'E2E_WORKSPACE': remote + '/workspace', 'E2E_MODEL': ARGS.model,
            'E2E_RUN_LLM': '1' if MODEL_REQUIRED else '0',
            'E2E_REQUIRE_LLM': '1' if MODEL_REQUIRED else '0', 'E2E_LLM_TIMEOUT': '420',
        })
        if TEMPLATE in {'droid', 'qwen-code', 'gemini'}:
            child_env.update({'E2E_BASE_DIR': remote + '/workspace', 'E2E_REQUIRE_CLI': '1'})
        child = await asyncio.create_subprocess_exec(
            sys.executable, str(ROOT / TEMPLATE / 'e2e_test.py'),
            env=child_env, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
        )
        output, _ = await asyncio.wait_for(child.communicate(), 540)
        text = scrub(output.decode(errors='replace')).replace(sb.id, '[OWNED_SANDBOX]')
        (OUT / (TEMPLATE + '-express-runtime.log')).write_text(text)
        record('remote HTTP suite' + (' with real model required' if MODEL_REQUIRED else ''), child.returncode == 0,
               f'exit={child.returncode}; PASS lines={sum(line.startswith(("[PASS]", "PASS ")) for line in text.splitlines())}; FAIL lines={text.count("[FAIL]")}')
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
