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
from pathlib import Path
import secrets
import shlex
import subprocess
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


def require(value, label):
    if not value:
        raise AssertionError(label)


class CLI:
    def __init__(self, executable, provider, env):
        self.command = shlex.split(executable)
        if not self.command:
            raise ValueError('ABX_BIN must select an installed CLI')
        self.provider, self.env = provider, env

    def run(self, args, timeout=300, json_output=True):
        proc = subprocess.run(self.command + ['--provider', self.provider]
            + (['--json'] if json_output else []) + args,
            env=self.env, stdin=subprocess.DEVNULL, capture_output=True,
            text=True, timeout=timeout)
        if proc.returncode:
            # Raw output can contain resource IDs or secrets; let the CLI journal
            # provide recovery and retain only the failed operation in this report.
            raise RuntimeError(f'CLI {args[0]} failed (exit {proc.returncode})')
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


async def cleanup_prepared(entries, cli, alias):
    """Delete only exact receipt-owned artifacts; unfamiliar registries stay pending."""
    import httpx
    done = set()
    failures = 0
    for entry in entries:
        if entry['kind'] == 'sandbox' or entry.get('state') == 'deleted':
            continue
        reference = entry.get('id')
        correlation = str(entry.get('correlation_key', ''))
        if not reference or alias not in correlation:
            continue
        try:
            if entry['kind'] == 'template' and cli.provider == 'alicloud-express':
                await asyncio.to_thread(cli.run, ['template', 'delete', reference, '--yes'], json_output=False)
                inventory = await asyncio.to_thread(cli.run, ['template', 'list', '--format', 'json'])
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
                    require(namespace == os.environ.get('ACR_NAMESPACE') and name.startswith(alias + '-'), 'owned ACR repository')
                    require(os.environ.get('ALIBABA_CLOUD_REGION_ID', 'cn-hangzhou') == 'cn-hangzhou', 'ACR region')
                    await asyncio.to_thread(delete_absent, '/repos/' + urllib.parse.quote(namespace, safe='') + '/'
                        + urllib.parse.quote(name, safe='') + '/tags/' + urllib.parse.quote(tag, safe=''))
                else:
                    continue
            else:
                continue
            done.add(entry['intent_id'])
        except Exception:
            failures += 1
    return done, failures


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
    cli = CLI(args.abx, args.provider, env)
    report = {'result': 'FAIL', 'template': args.template, 'provider': args.provider,
        'scope': 'public CLI source launch + manifest smoke via host CLI, Python and HTTP; no real-model acceptance',
        'source': args.source or f'Alibaba-Agent-Sandbox/awesome-templates//{args.template}',
        'manifest_sha256': hashlib.sha256((source / 'template.yaml').read_bytes()).hexdigest(),
        'cli_version': cli.run(['--version'], json_output=False),
        'python_client_version': importlib.metadata.version('agent-sandbox-client'),
        'checks': [], 'cleanup': {'sandbox': 'not created', 'prepared_artifacts': 'not checked'}}
    alias = 'public-e2e-' + secrets.token_hex(8)
    journal_dir = Path.home() / '.abx' / 'resource-journal'
    original_journals = set(journal_dir.glob('*.json'))
    launch = None
    sandbox = None
    client = None
    try:
        launch = await asyncio.to_thread(cli.run,
            ['template', 'launch', report['source'], '--workflow', manifest['default_workflow'],
             '--alias', alias, '--timeout', str(args.build_timeout), '--sandbox-timeout', '1800', '--yes'],
            args.build_timeout + 300)
        require(launch.get('manifest_digest') == 'sha256:' + report['manifest_sha256'],
                'launched manifest must match the selected local verifier input')
        require(launch.get('provider') == args.provider, 'selected provider must be retained')
        report['input_receipt'] = {key: launch.get(key) for key in
            ['manifest_digest', 'source_digest', 'provider_digest', 'provider_snapshot_digest', 'plan_digest', 'build_profile']}
        report['checks'].append('unchanged source launched by installed CLI')
        sandbox = await ProviderSandbox.connect(launch['sandbox_id'], provider=args.provider)
        client = await sandbox.application_client(9000, token=env['ABX_SERVER_TOKEN'], timeout=180)
        endpoint, headers = await sandbox.network.resolve(9000)
        require(all(key.lower() != 'authorization' for key in headers),
                'application and gateway Authorization must not overwrite one another')
        headers = {**headers, 'Authorization': 'Bearer ' + env['ABX_SERVER_TOKEN']}
        async with httpx.AsyncClient(timeout=180, follow_redirects=False, trust_env=False) as http:
            for index, case in enumerate(cases):
                name, values = case['command'], case.get('args', {})
                result = await asyncio.to_thread(cli.run, ['run', sandbox.id, name, '--json-args', json.dumps(values)])
                observed = result['result']
                if 'expect' in case:
                    require(matches(observed, case['expect']), f'CLI smoke {index} result')
                else:
                    require(observed is not None and observed != '', f'CLI smoke {index} nonempty result')
                result = await client.commands.run(name, **values)
                require(matches(result, case['expect']) if 'expect' in case else result is not None and result != '', f'Python smoke {index} result')
                response = await http.post(command_url(endpoint, name), headers=headers, json=values)
                require(response.status_code == 200, f'HTTP smoke {index} status')
                http_result = response.json()['result']
                require(matches(http_result, case['expect']) if 'expect' in case else http_result is not None and http_result != '', f'HTTP smoke {index} result')
                report['checks'].append({'smoke': index, 'command': name, 'consumers': ['cli', 'python', 'host-http'], 'has_expected_result': 'expect' in case})
            # Test service authentication without dropping required gateway headers.
            unauthorized = await http.post(command_url(endpoint, cases[0]['command']),
                headers={**headers, 'Authorization': 'Bearer intentionally-wrong'}, json=cases[0].get('args', {}))
            require(unauthorized.status_code == 401, 'wrong service token must be rejected')
        report['checks'].append('service authentication rejects wrong token')
        observed = await sandbox.files.read('/home/user/app/commands.py')
        require(observed.encode() == (source / 'commands.py').read_bytes(), 'runtime command bytes match selected source')
        result = await sandbox.commands.run('python3 -c "print(21 * 2)"', timeout=30)
        require(result.exit_code == 0 and result.stdout.strip() == '42', 'SDK exec result')
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
        if isinstance(failure, AssertionError):
            report['failed_check'] = str(failure)
    finally:
        if client is not None:
            await client.close()
        journals = []
        for path in set(journal_dir.glob('*.json')) - original_journals:
            data = json.loads(path.read_text())
            if data.get('provider') == args.provider and any(
                str(entry.get('correlation_key', '')).startswith(alias + '-') for entry in data.get('entries', [])):
                journals.append(data)
        entries = [entry for journal in journals for entry in journal.get('entries', [])]
        ids = {entry['id'] for entry in entries if entry['kind'] == 'sandbox' and entry.get('id')}
        if launch:
            ids.add(launch['sandbox_id'])
        cleanup_failed = False
        for sid in ids:
            owned = None
            try:
                try:
                    owned = await ProviderSandbox.connect(sid, provider=args.provider)
                except SandboxNotFoundError:
                    continue
                await owned.kill()
                # Read independently through a new connection; DELETE acknowledgement is insufficient.
                try:
                    remaining = await ProviderSandbox.connect(sid, provider=args.provider)
                except SandboxNotFoundError:
                    pass
                else:
                    await remaining.close()
                    raise AssertionError('owned sandbox remains after deletion')
            except Exception:
                cleanup_failed = True
            finally:
                if owned:
                    await owned.close()
        if sandbox:
            await sandbox.close()
        report['cleanup']['sandbox'] = 'failed' if cleanup_failed else ('confirmed absent' if ids else 'not observed')
        prepared_done, prepared_failures = await cleanup_prepared(entries, cli, alias)
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
