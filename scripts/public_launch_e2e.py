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


def controller_label(value, secrets=()):
    """Keep bounded controller check labels without private locations or credentials."""
    for secret in secrets:
        if secret:
            value = value.replace(secret, '[FIXTURE]')
    value = re.sub(r'https?://\S+|/[A-Za-z0-9_.@%/+-]+', '[LOCATION]', value)
    value = re.sub(r'\b[0-9a-fA-F-]{16,}\b', '[ID]', value)
    return value[:300]


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
        ('Template cannot launch on this provider: provider-mismatch.', 'provider-mismatch'),
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

    @property
    def journal_directory(self):
        return Path(self.env.get('HOME') or Path.home()) / '.abx' / 'resource-journal'

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


async def verify_cli_io(cli, sandbox, alias, private):
    """Exercise published CLI process/transfer paths against independent SDK reads."""
    executed = await asyncio.to_thread(cli.run, ['exec', sandbox.id, '--', 'python3', '-c', 'print(21 * 2)'])
    require(isinstance(executed, dict) and executed.get('exit_code') == 0
            and isinstance(executed.get('stdout'), str) and executed['stdout'].strip() == '42',
            'CLI exec JSON result')
    nonce = secrets.token_hex(8)
    remote = '/tmp/' + alias + '-cli-' + nonce + '.txt'
    uploaded = private / ('cli-upload-' + nonce + '.txt')
    downloaded = private / ('cli-download-' + nonce + '.txt')
    payload = ('owned CLI transfer\n中文 snowman ☃\n' + nonce + '\n').encode('utf-8')
    with uploaded.open('xb') as stream:
        stream.write(payload)
    try:
        await asyncio.to_thread(cli.run, ['upload', sandbox.id, str(uploaded), remote], json_output=False)
        require((await sandbox.files.read(remote)).encode('utf-8') == payload, 'SDK reads exact CLI uploaded bytes')
        await asyncio.to_thread(cli.run, ['sandbox', 'files', 'stat', sandbox.id, '--path', remote], json_output=False)
        await asyncio.to_thread(cli.run, ['download', sandbox.id, remote, str(downloaded)], json_output=False)
        require(downloaded.read_bytes() == payload, 'CLI download preserves uploaded bytes')
        await asyncio.to_thread(cli.run, ['sandbox', 'files', 'rm', sandbox.id, '--path', remote, '--yes'], json_output=False)
        require(not await sandbox.files.exists(remote), 'SDK confirms CLI file deletion')
    finally:
        if await sandbox.files.exists(remote):
            await sandbox.files.remove(remote)
        uploaded.unlink(missing_ok=True)
        downloaded.unlink(missing_ok=True)
    require(not await sandbox.files.exists(remote), 'owned CLI transfer file cleanup')


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
    from template_application import validate_v5
    problems = validate_v5(manifest, source)
    if problems:
        raise ValueError('invalid template launch manifest: ' + '; '.join(problems))
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


def export_owned_image(entries, alias, source, directory, provenance, runtime_version=None, public_source_commit=None, source_snapshot_digest=None):
    """Export only the image built by this successful launch, before owned cleanup."""
    from server_package import server_version
    require(not directory.exists(), 'image export directory must be fresh')
    images = {}
    for entry in entries:
        tag = str(entry.get('correlation_key', ''))
        if entry.get('kind') != 'image' or not tag.rsplit(':', 1)[-1].startswith(alias + '-'):
            continue
        if '/' in tag and not tag.startswith('localhost:5000/'):
            continue
        proc = subprocess.run(['docker', 'image', 'inspect', '--format', '{{.Id}}', tag],
                              capture_output=True, text=True, timeout=30)
        require(proc.returncode == 0, 'owned export image exists')
        images[proc.stdout.strip()] = tag
    require(len(images) == 1, 'exactly one owned image must be exported')
    image_id, tag = next(iter(images.items()))
    require(re.fullmatch(r'sha256:[0-9a-f]{64}', image_id), 'owned export image identity')
    require(runtime_version == server_version(source), 'export image server matches declared public package')
    directory.mkdir(parents=True)
    archive = directory / (source.name + '-image.tar')
    subprocess.run(['docker', 'image', 'save', '--output', str(archive), tag],
                   check=True, capture_output=True, timeout=600)
    with archive.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    (directory / (archive.name + '.sha256')).write_text(digest + '  ' + archive.name + '\n')
    revision = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    metadata = {'format': 'docker-archive', 'origin': 'public-template-launch',
        'template': source.name, 'repository': 'Alibaba-Agent-Sandbox/awesome-templates',
        'checkout_commit': public_source_commit or revision, 'source_head_commit': public_source_commit or revision,
        'verifier_commit': revision, 'public_source_commit': public_source_commit,
        'source_snapshot_digest': source_snapshot_digest,
        'workflow_run_id': os.environ.get('GITHUB_RUN_ID'),
        'server_package_version': runtime_version, 'local_image_id': image_id,
        'archive_sha256': digest, 'installed_packages': provenance,
        'acceptance': 'published CLI launch and manifest smoke on OpenSandbox; no Express or model acceptance'}
    (directory / (source.name + '-image-metadata.json')).write_text(json.dumps(metadata, indent=2) + '\n')
    return {'archive_sha256': digest, 'image_config_sha256': image_id.removeprefix('sha256:')}


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


def installation_provenance(env, client_version, server_version):
    """Keep source candidates distinct from published-package acceptance."""
    distribution = env.get('PUBLIC_LAUNCH_DISTRIBUTION') or 'published'
    if distribution not in {'published', 'source'}:
        raise ValueError('unknown installation distribution')
    result = {
        'distribution': distribution,
        'cli': {'name': '@agent-sandbox/cli', 'version': env['PUBLIC_CLI_VERSION'],
                'source_ref': env.get('PUBLIC_LAUNCH_CLI_REF')},
        'python_client': {'name': 'agent-sandbox-client', 'version': client_version,
                'source_ref': env.get('PUBLIC_LAUNCH_SDK_REF')},
        'python_server': {'name': 'agent-sandbox-server', 'version': server_version,
                'source_ref': env.get('PUBLIC_LAUNCH_SDK_REF')},
        'provider_source_ref': env.get('PUBLIC_LAUNCH_PROVIDERS_REF'),
        'template_source_ref': env.get('PUBLIC_LAUNCH_TEMPLATES_REF'),
    }
    if distribution == 'published':
        result['cli']['registry'] = 'https://registry.npmjs.org'
        for name in ['python_client', 'python_server']:
            result[name]['registry'] = 'https://pypi.org/simple'
    return result


async def verify(args):
    from agent_sandbox import ProviderSandbox
    from agent_sandbox.models.errors import SandboxNotFoundError
    import httpx

    source, manifest, cases = load_plan(args.template)
    env = os.environ.copy()
    # This is a generated application credential for this run, never a model key.
    for key, value in manifest.get('env', {}).items():
        if value == '':
            env.pop(key, None)
    env['ABX_SERVER_TOKEN'] = secrets.token_urlsafe(32)
    from template_http_acceptance import fixture_environment, run_controller
    server_fixture, controller_fixture, fixture_proof = fixture_environment(args.template)
    env.update(server_fixture)
    cli = CLI(args.abx, args.provider, env)
    report = {'result': 'FAIL', 'template': args.template, 'provider': args.provider,
        'scope': 'public CLI source launch + manifest smoke via host CLI, Python and HTTP; no real-model acceptance',
        'source': ('local-candidate/' + args.template) if args.source and Path(args.source).is_dir() else (args.source or f'Alibaba-Agent-Sandbox/awesome-templates//{args.template}'),
        'manifest_sha256': hashlib.sha256((source / 'template.yaml').read_bytes()).hexdigest(),
        'cli_version': cli.run(['--version'], json_output=False),
        'python_client_version': importlib.metadata.version('agent-sandbox-client'),
        'checks': [], 'cleanup': {'sandbox': 'not created', 'prepared_artifacts': 'not checked'}}
    if env.get('PUBLIC_CLI_VERSION') and env.get('PUBLIC_SDK_VERSION'):
        report['installed_packages'] = installation_provenance(
            env, importlib.metadata.version('agent-sandbox-client'),
            importlib.metadata.version('agent-sandbox-server'))
    report['test_configuration'] = fixture_proof
    alias = 'public-e2e-' + secrets.token_hex(8)
    report['run_alias'] = alias
    if args.provider == 'opensandbox':
        report['endpoint_mode'] = 'server-proxy' if env.get('ABX_OPENSANDBOX_USE_SERVER_PROXY', '').lower() in {'1', 'true', 'yes', 'on'} else 'direct'
    journal_dir = cli.journal_directory
    original_journals = set(journal_dir.glob('*.json'))
    launch = None
    sandbox = None
    client = None
    phase = 'public-source-resolution'
    public_source_commit = None
    try:
        if not args.source:
            resolved = await asyncio.to_thread(subprocess.run,
                ['git', 'ls-remote', '--exit-code', 'https://github.com/Alibaba-Agent-Sandbox/awesome-templates.git', 'HEAD'],
                capture_output=True, text=True, timeout=60, check=True)
            require(re.fullmatch(r'[0-9a-f]{40}\s+HEAD\s*', resolved.stdout), 'public Git HEAD must resolve to an immutable commit')
            public_source_commit = resolved.stdout.split()[0]
            report['requested_source'] = report['source']
            report['source'] += '@' + public_source_commit
            report['public_source_commit'] = public_source_commit
            report['verifier_commit'] = env.get('PUBLIC_LAUNCH_TEMPLATES_REF')
            if report.get('installed_packages'):
                report['installed_packages']['template_verifier_ref'] = env.get('PUBLIC_LAUNCH_TEMPLATES_REF')
                report['installed_packages']['template_source_ref'] = public_source_commit
        phase = 'template-launch'
        launch = await asyncio.to_thread(cli.run,
            ['template', 'launch', args.source or report['source'],
             '--alias', alias, '--timeout', str(args.build_timeout), '--sandbox-timeout', '1800', '--yes'],
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
        phase = 'runtime-package'
        version = await sandbox.commands.run('python3 -c "import importlib.metadata; print(importlib.metadata.version(\'agent-sandbox-server\'))"', timeout=30)
        require(version.exit_code == 0 and re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:a[0-9]+)?', version.stdout.strip()),
                'runtime server version is a release version')
        from server_package import server_version
        require(version.stdout.strip() == server_version(source), 'runtime server matches declared public package')
        report['server_package_version'] = version.stdout.strip()
        phase = 'cli-process-and-files'
        await verify_cli_io(cli, sandbox, alias, cli.private_directory)
        report['checks'].append('CLI exec, stat, upload/download exact bytes and independent SDK file cleanup')

        if args.application_controller:
            phase = 'application-controller'
            urls = {}
            report['port_endpoint_layout'] = []
            for port in manifest.get('ports', [9000]):
                url, port_headers = await sandbox.network.resolve(port)
                require(port_headers == gateway_headers, 'HTTP controller gateway authentication must match across declared ports')
                urls[port] = url
                parts = urllib.parse.urlsplit(url)
                report['port_endpoint_layout'].append({'port': port, 'scheme': parts.scheme,
                    'has_path_prefix': bool(parts.path.strip('/')), 'has_query': bool(parts.query),
                    'gateway_header_count': len(port_headers)})
            report['http_acceptance'] = await asyncio.to_thread(run_controller, source, urls,
                cli.private_directory, controller_fixture, token=env['ABX_SERVER_TOKEN'], gateway_headers=gateway_headers)
            if not report['http_acceptance']['passed']:
                labels = [line for line in (cli.private_directory / 'http.log').read_text().splitlines()
                          if line.startswith(('[FAIL]', '[SKIP]'))]
                report['http_diagnostics'] = [controller_label(line, [env['ABX_SERVER_TOKEN'], *server_fixture.values()]) for line in labels[:12]]
            require(report['http_acceptance']['passed'], 'template application HTTP controller')
        if args.export_image_dir:
            phase = 'export-owned-image'
            require(args.provider == 'opensandbox', 'image export requires the disposable OpenSandbox backend')
            entries = [entry for path in set(journal_dir.glob('*.json')) - original_journals
                       for entry in json.loads(path.read_text()).get('entries', [])]
            report['image_export'] = await asyncio.to_thread(export_owned_image, entries, alias, source,
                args.export_image_dir, report.get('installed_packages'), report['server_package_version'], public_source_commit, launch.get('source_digest'))
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
    parser.add_argument('--application-controller', action='store_true', help='run the unchanged full template HTTP controller after smoke')
    parser.add_argument('--export-image-dir', type=Path, help='save the exact owned OpenSandbox image before cleanup')
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
