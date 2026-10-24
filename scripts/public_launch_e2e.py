#!/usr/bin/env python3
"""Test an unchanged template through installed CLI launch, host CLI/SDK/HTTP.

No guest curl, Docker bridge lookup, source rewriting, or provider fallback.
Reports exclude credentials, native resource IDs and command output. The CLI's
private resource journal owns recovery after an ambiguous launch failure.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import os
import re
from pathlib import Path
import secrets
import shlex
import subprocess
import tempfile
import sys
import urllib.parse

import yaml

from select_image_templates import ROOT, catalog_names


def matches(actual, expected):
    if isinstance(actual, str) and isinstance(expected, str):
        return actual.strip() == expected.strip()
    return actual == expected


def command_url(base, name):
    parts = urllib.parse.urlsplit(base)
    if parts.scheme not in {'http', 'https'} or not parts.hostname or parts.username or parts.password or parts.fragment:
        raise ValueError('provider must return an absolute HTTP endpoint without user information')
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc,
        parts.path.rstrip('/') + '/commands/' + urllib.parse.quote(name, safe=''), parts.query, ''))


def application_headers(gateway_headers, token):
    require(all(key.lower() != 'authorization' for key in gateway_headers),
            'application and gateway Authorization must not overwrite one another')
    headers = {**gateway_headers, 'Authorization': 'Bearer ' + token}
    if all(key.lower() != 'x-access-token' for key in gateway_headers):
        headers['X-Access-Token'] = token
    return headers


class CheckFailed(AssertionError):
    """A runner-owned, controlled check label, never a dependency exception."""


def require(value, label):
    if not value:
        raise CheckFailed(label)


def safe_failure_label(failure):
    return str(failure) if isinstance(failure, (CheckFailed, CLIError)) else None


def safe_diagnostics(failure):
    """Only controlled categories, numeric HTTP status and stable SDK codes escape."""
    if isinstance(failure, CLIError):
        return failure.diagnostics
    details = {}
    code = getattr(failure, 'code', None)
    if isinstance(code, str) and re.fullmatch(r'E[0-9]{4}', code):
        details['code'] = code
    response = getattr(failure, 'response', None)
    status = getattr(response, 'status_code', None)
    if type(status) is int and 100 <= status <= 599:
        details['http_status'] = status
    match = re.search(r'\bHTTP(?: status)?[ :]+([1-5][0-9]{2})\b', str(failure))
    if match:
        details['http_status'] = int(match.group(1))
    return details


def cli_diagnostics(output):
    try:
        payload = json.loads(output)
    except (ValueError, TypeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    details = {}
    code = payload.get('code')
    if isinstance(code, str) and re.fullmatch(r'E[0-9]{4}', code):
        details['code'] = code
    message = payload.get('message', '')
    if not isinstance(message, str):
        return details
    for prefix, category in [
        ('Template startup failed', 'template-startup'),
        ('Sandbox creation/session binding failed', 'sandbox-session-binding'),
        ('Sandbox creation has an uncertain outcome', 'sandbox-creation-uncertain'),
        ('Template preparation failed', 'template-preparation'),
    ]:
        if message.startswith(prefix):
            details['category'] = category
            break
    match = re.search(r'\bHTTP(?: status)?[ :]+([1-5][0-9]{2})\b', message)
    if match:
        details['http_status'] = int(match.group(1))
    return details


class CLIError(RuntimeError):
    def __init__(self, operation, returncode, output):
        super().__init__(f'CLI {operation} failed (exit {returncode})')
        self.diagnostics = cli_diagnostics(output)


class CLI:
    def __init__(self, executable, provider, env):
        self.command = shlex.split(executable)
        if not self.command:
            raise ValueError('ABX_BIN must select an installed CLI')
        self.provider, self.env = provider, env
        self.private_directory = Path(tempfile.mkdtemp(prefix="abx-public-launch-"))
        self.call_count = 0

    def run(self, args, timeout=300, json_output=True, native=False):
        proc = subprocess.run(self.command + (['--native'] if native else []) + ['--provider', self.provider]
            + (['--json'] if json_output else []) + args,
            env=self.env, stdin=subprocess.DEVNULL, capture_output=True,
            text=True, timeout=timeout)
        self.call_count += 1
        log = self.private_directory / f'cli-{self.call_count}.log'
        with log.open('x') as stream:
            os.chmod(log, 0o600)
            stream.write(proc.stdout + '\n' + proc.stderr)
        if proc.returncode:
            # Raw output can contain resource IDs or secrets; let the CLI journal
            # provide recovery and retain only the failed operation in this report.
            raise CLIError(args[0], proc.returncode, proc.stdout)
        return json.loads(proc.stdout) if json_output else proc.stdout.strip()


def source_names(root=ROOT):
    return [name for name in catalog_names(root)
            if (root / name / 'Dockerfile').is_file()]


def load_plan(name, root=ROOT):
    if name not in source_names(root):
        raise ValueError('select an existing source template from the catalog')
    source = root / name
    manifest = yaml.safe_load((source / 'template.yaml').read_text())
    cases = manifest.get('smoke') or []
    if not cases or any(not isinstance(case.get('command'), str) for case in cases):
        raise ValueError('public launch acceptance needs named smoke cases')
    workflow = manifest['workflows'][manifest['default_workflow']]
    if workflow['input'] != 'source' or workflow['kind'] != 'application':
        raise ValueError('this runner verifies source application workflows only')
    return source, manifest, cases


def json_contains(value, target):
    if isinstance(value, dict):
        return any(json_contains(item, target) for item in value.values())
    if isinstance(value, list):
        return any(json_contains(item, target) for item in value)
    return value == target


async def cleanup_prepared(entries, cli, alias, diagnostics=None):
    """Delete only exact receipt-owned artifacts; unfamiliar registries stay pending."""
    import httpx
    done = set()
    failures = 0
    for entry in entries:
        if entry['kind'] == 'sandbox' or entry.get('state') == 'deleted':
            continue
        reference = entry.get('id')
        correlation = str(entry.get('correlation_key', ''))
        if not reference or alias + '-' not in correlation:
            continue
        try:
            if entry['kind'] == 'template' and cli.provider == 'alicloud-express':
                await asyncio.to_thread(cli.run, ['template', 'delete', reference, '--yes'], json_output=False, native=True)
                inventory = await asyncio.to_thread(cli.run, ['template', 'list'], native=True)
                require(not json_contains(inventory, reference), 'owned template deletion readback')
            elif entry['kind'] == 'image':
                # Local Docker tags have no registry hostname; never remove by image ID.
                if '/' not in correlation:
                    proc = await asyncio.to_thread(subprocess.run, ['docker', 'image', 'rm', correlation],
                        capture_output=True, text=True, timeout=60)
                    require(proc.returncode == 0, 'owned local image removal')
                    check = await asyncio.to_thread(subprocess.run, ['docker', 'image', 'inspect', correlation],
                        capture_output=True, text=True, timeout=30)
                    require(check.returncode != 0 and 'No such image' in check.stderr,
                            'owned local image absence')
                elif correlation.startswith('localhost:5000/') and cli.provider == 'opensandbox':
                    # This registry is explicitly created by the disposable CI setup.
                    repository, tag = correlation.removeprefix('localhost:5000/').rsplit(':', 1)
                    require(tag.startswith(alias + '-'), 'owned local registry tag')
                    url = 'http://localhost:5000/v2/' + repository + '/manifests/'
                    async with httpx.AsyncClient(timeout=30, follow_redirects=False, trust_env=False) as http:
                        headers = {'Accept': 'application/vnd.docker.distribution.manifest.v2+json, application/vnd.oci.image.manifest.v1+json'}
                        response = await http.get(url + tag, headers=headers)
                        if response.status_code != 404:
                            require(response.status_code == 200, 'owned registry manifest read')
                            digest = response.headers.get('Docker-Content-Digest', '')
                            require(digest.startswith('sha256:') and len(digest) == 71, 'owned registry digest')
                            if '@' in reference:
                                require(reference.endswith('@' + digest), 'owned registry digest match')
                            removed = await http.delete(url + digest)
                            require(removed.status_code in {202, 404}, 'owned registry delete')
                        require((await http.get(url + tag, headers=headers)).status_code == 404,
                                'owned registry absence')
                    proc = await asyncio.to_thread(subprocess.run, ['docker', 'image', 'rm', correlation],
                        capture_output=True, text=True, timeout=60)
                    # The same tag is recorded for build and push; a duplicate may already be gone.
                    require(proc.returncode == 0 or 'No such image' in proc.stderr, 'owned local tag removal')
                elif cli.provider == 'alicloud-express' and correlation.startswith('registry.cn-hangzhou.aliyuncs.com/'):
                    # Reuse the repository's existing signed ACR DELETE + GET-404 verifier.
                    from canonical_express_review import delete_absent
                    repository, tag = correlation.split('/', 1)[1].rsplit(':', 1)
                    namespace, name = repository.split('/', 1)
                    # The repository is shared (usually the manifest name); only the
                    # per-launch tag is owned. Never delete the repository itself.
                    require(namespace == os.environ.get('ACR_NAMESPACE') and tag.startswith(alias + '-'), 'owned ACR tag')
                    require(os.environ.get('ALIBABA_CLOUD_REGION_ID', 'cn-hangzhou') == 'cn-hangzhou', 'ACR region')
                    await asyncio.to_thread(delete_absent, '/repos/' + urllib.parse.quote(namespace, safe='') + '/'
                        + urllib.parse.quote(name, safe='') + '/tags/' + urllib.parse.quote(tag, safe=''))
                else:
                    continue
            else:
                continue
            done.add(entry['intent_id'])
        except Exception as failure:
            failures += 1
            if diagnostics is not None:
                diagnostics.append({'kind': entry['kind'], 'failure_type': type(failure).__name__, **safe_diagnostics(failure)})
    return done, failures


async def cleanup_before_close(release_resources, client, sandbox):
    """Local HTTP close errors must never prevent deleting cloud resources."""
    errors = []
    try:
        await release_resources()
    except Exception as failure:
        errors.append(type(failure).__name__)
    finally:
        for target, method in [(client, 'aclose'), (sandbox, 'close')]:
            if target is not None:
                try:
                    await getattr(target, method)()
                except Exception as failure:
                    errors.append(type(failure).__name__)
    return errors


async def delete_sandbox(api, sid, provider, not_found, delay=1):
    try:
        await api.kill_by_id(sid, provider=provider)
    except not_found:
        pass
    for attempt in range(10):
        try:
            await api.get_info_by_id(sid, provider=provider)
        except not_found:
            return
        if attempt < 9:
            await asyncio.sleep(delay)
    raise AssertionError('owned sandbox remains after deletion')


async def verify(args):
    from agent_sandbox import ProviderSandbox
    from agent_sandbox.models.errors import SandboxNotFoundError
    import httpx

    source, manifest, cases = load_plan(args.template)
    if args.template == 'qwen-code':
        # Extra README operation; do not modify the fetched template manifest.
        cases.append({'command': 'qwen_setup_check', 'args': {}})
    env = os.environ.copy()
    # This is a generated application credential for this run, never a model key.
    for key, value in manifest.get('env', {}).items():
        if value == '':
            env.pop(key, None)
    env['ABX_SERVER_TOKEN'] = secrets.token_urlsafe(32)
    cli = CLI(args.abx, args.provider, env)
    report = {'result': 'FAIL', 'template': args.template, 'provider': args.provider,
        'scope': 'public CLI source launch + manifest smoke via host CLI, Python and HTTP; no real-model acceptance',
        'source': ('local-candidate/' + args.template) if args.source and Path(args.source).is_dir() else (args.source or f'Alibaba-Agent-Sandbox/awesome-templates//{args.template}'),
        'manifest_sha256': hashlib.sha256((source / 'template.yaml').read_bytes()).hexdigest(),
        'cli_version': cli.run(['--version'], json_output=False),
        'python_client_version': importlib.metadata.version('agent-sandbox-client'),
        'checks': [], 'cleanup': {'sandbox': 'not created', 'prepared_artifacts': 'not checked'}}
    if env.get('PUBLIC_CLI_VERSION') and env.get('PUBLIC_SDK_VERSION'):
        report['installed_packages'] = {
            'cli': {'name': '@agent-sandbox/cli', 'version': env['PUBLIC_CLI_VERSION'],
                    'registry': 'https://registry.npmjs.org', 'source_ref': env.get('PUBLIC_LAUNCH_CLI_REF')},
            'python_client': {'name': 'agent-sandbox-client', 'version': importlib.metadata.version('agent-sandbox-client'),
                    'registry': 'https://pypi.org/simple', 'source_ref': env.get('PUBLIC_LAUNCH_SDK_REF')},
            'python_server': {'name': 'agent-sandbox-server', 'version': importlib.metadata.version('agent-sandbox-server'),
                    'registry': 'https://pypi.org/simple', 'source_ref': env.get('PUBLIC_LAUNCH_SDK_REF')},
            'provider_source_ref': env.get('PUBLIC_LAUNCH_PROVIDERS_REF'),
        }
    alias = 'public-e2e-' + secrets.token_hex(8)
    report['run_alias'] = alias
    if args.provider == 'opensandbox':
        report['endpoint_mode'] = 'server-proxy' if env.get('ABX_OPENSANDBOX_USE_SERVER_PROXY', '').lower() in {'1', 'true', 'yes', 'on'} else 'direct'
    journal_dir = Path.home() / '.abx' / 'resource-journal'
    original_journals = set(journal_dir.glob('*.json'))
    launch = None
    sandbox = None
    client = None
    phase = 'template-launch'
    try:
        launch = await asyncio.to_thread(cli.run,
            ['template', 'launch', args.source or report['source'], '--workflow', manifest['default_workflow'],
             '--alias', alias, '--timeout', str(args.build_timeout), '--sandbox-timeout', '900', '--yes'],
            args.build_timeout + 300)
        require(launch.get('manifest_digest') == 'sha256:' + report['manifest_sha256'],
                'launched manifest must match the selected local verifier input')
        require(launch.get('provider') == args.provider, 'selected provider must be retained')
        report['input_receipt'] = {key: launch.get(key) for key in
            ['manifest_digest', 'source_digest', 'provider_digest', 'provider_snapshot_digest', 'plan_digest', 'build_profile']}
        report['checks'].append('unchanged source launched by installed CLI')
        phase = 'sdk-connect'
        sandbox = await ProviderSandbox.connect(launch['sandbox_id'], provider=args.provider)
        phase = 'application-client'
        client = await sandbox.application_client(9000, token=env['ABX_SERVER_TOKEN'], timeout=180)
        phase = 'endpoint-resolution'
        endpoint, gateway_headers = await sandbox.network.resolve(9000)
        headers = application_headers(gateway_headers, env['ABX_SERVER_TOKEN'])
        async with httpx.AsyncClient(timeout=180, follow_redirects=False, trust_env=False) as http:
            for index, case in enumerate(cases):
                name, values = case['command'], case.get('args', {})
                phase = 'cli-command'
                result = await asyncio.to_thread(cli.run, ['run', sandbox.id, name, '--json-args', json.dumps(values)])
                observed = result['result']
                if 'expect' in case:
                    require(matches(observed, case['expect']), f'CLI smoke {index} result')
                else:
                    require(observed is not None and observed != '', f'CLI smoke {index} nonempty result')
                phase = 'python-command'
                result = await client.commands.run(name, **values)
                require(matches(result, case['expect']) if 'expect' in case else result is not None and result != '', f'Python smoke {index} result')
                phase = 'http-command'
                response = await http.post(command_url(endpoint, name), headers=headers, json=values)
                require(response.status_code == 200, f'HTTP smoke {index} status')
                http_result = response.json()['result']
                require(matches(http_result, case['expect']) if 'expect' in case else http_result is not None and http_result != '', f'HTTP smoke {index} result')
                if name == 'qwen_setup_check':
                    for value in [observed, result, http_result]:
                        require(isinstance(value, dict) and value.get('installed') is True
                                and value.get('version') == '0.23.0' and value.get('api_key_set') is False,
                                'documented keyless Qwen setup result')
                    report['checks'].append('README qwen_setup_check: installed and pinned version, no model key; three consumers')
                report['checks'].append({'smoke': index, 'command': name, 'consumers': ['cli', 'python', 'host-http'], 'has_expected_result': 'expect' in case})
            # Test service authentication without dropping required gateway headers.
            phase = 'authentication-negative'
            unauthorized = await http.post(command_url(endpoint, cases[0]['command']),
                headers=application_headers(gateway_headers, 'intentionally-wrong'), json=cases[0].get('args', {}))
            require(unauthorized.status_code == 401, 'wrong service token must be rejected')
        report['checks'].append('service authentication rejects wrong token')
        phase = 'source-identity'
        observed = await sandbox.files.read('/home/user/app/commands.py')
        require(observed.encode() == (source / 'commands.py').read_bytes(), 'runtime command bytes match selected source')
        phase = 'sdk-exec'
        result = await sandbox.commands.run('python3 -c "print(21 * 2)"', timeout=30)
        require(result.exit_code == 0 and result.stdout.strip() == '42', 'SDK exec result')
        phase = 'sdk-files'
        path = '/tmp/' + alias + '.txt'
        await sandbox.files.write(path, 'owned acceptance file\n')
        require(await sandbox.files.read(path) == 'owned acceptance file\n', 'SDK file readback')
        await sandbox.files.remove(path)
        require(not await sandbox.files.exists(path), 'SDK file deletion readback')
        report['checks'].extend(['runtime source identity', 'SDK exec and file round trip'])
        report['application_result'] = 'PASS'
    except Exception as failure:
        report['application_result'] = 'FAIL'
        # Exceptions from remote SDKs can contain private data; save type only.
        report['failure_type'] = type(failure).__name__
        report['failed_phase'] = phase
        report['diagnostics'] = safe_diagnostics(failure)
        label = safe_failure_label(failure)
        if label is not None:
            report['failed_check'] = label
    finally:
        async def release_resources():
            journals = []
            for path in set(journal_dir.glob('*.json')) - original_journals:
                data = json.loads(path.read_text())
                if data.get('provider') == args.provider and any(
                    alias + '-' in str(entry.get('correlation_key', '')) for entry in data.get('entries', [])):
                    journals.append(data)
            entries = [entry for journal in journals for entry in journal.get('entries', [])]
            ids = {entry['id'] for entry in entries if entry['kind'] == 'sandbox' and entry.get('id')}
            if launch:
                ids.add(launch['sandbox_id'])
            cleanup_failed = False
            for sid in ids:
                try:
                    await delete_sandbox(ProviderSandbox, sid, args.provider, SandboxNotFoundError)
                except Exception:
                    cleanup_failed = True
            report['cleanup']['sandbox'] = 'failed' if cleanup_failed else ('confirmed absent' if ids else 'not observed')
            cleanup_diagnostics = []
            prepared_done, prepared_failures = await cleanup_prepared(entries, cli, alias, cleanup_diagnostics)
            report['cleanup']['diagnostics'] = cleanup_diagnostics
            cleanup_failed = cleanup_failed or prepared_failures > 0
            pending = [entry for entry in entries if entry['kind'] != 'sandbox' and entry.get('state') != 'deleted' and entry['intent_id'] not in prepared_done]
            unknown = [entry for entry in entries if entry.get('state') in {'intent', 'uncertain'}]
            report['cleanup']['prepared_artifacts'] = 'retained in private CLI journal' if pending else ('confirmed absent' if prepared_done else 'none observed')
            report['cleanup']['artifact_cleanup_failures'] = prepared_failures
            report['cleanup']['retained_artifact_count'] = len(pending)
            report['cleanup']['uncertain_count'] = len(unknown)
            # A successful application test cannot silently certify registry/template cleanup.
            if report.get('application_result') == 'PASS' and not cleanup_failed:
                report['result'] = 'PARTIAL' if pending or unknown or not journals else 'PASS'
        close_errors = await cleanup_before_close(release_resources, client, sandbox)
        if close_errors:
            report['result'] = 'FAIL'
            report['cleanup']['errors'] = close_errors
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x') as stream:
            json.dump(report, stream, indent=2)
            stream.write('\n')
    return 0 if report['result'] == 'PASS' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('template', nargs='?')
    parser.add_argument('--provider', choices=['alicloud-express', 'opensandbox'])
    parser.add_argument('--source', help='public Git source or local candidate directory; verifier inputs must match')
    parser.add_argument('--abx', default=os.environ.get('ABX_BIN', 'abx'))
    parser.add_argument('--build-timeout', type=int, default=1200)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--list', action='store_true', help='list all source templates without cloud operations')
    args = parser.parse_args()
    if args.list:
        print(json.dumps(source_names()))
        return 0
    if not args.template or not args.provider or not args.output:
        parser.error('template, --provider and --output are required')
    if args.output.exists():
        parser.error('output already exists; preserve earlier attempts')
    if not 1 <= args.build_timeout <= 3600:
        parser.error('--build-timeout must be between 1 and 3600 seconds')
    return asyncio.run(verify(args))


if __name__ == '__main__':
    raise SystemExit(main())
