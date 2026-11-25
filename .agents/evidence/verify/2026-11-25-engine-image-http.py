"""Temporary two-image HTTP verifier; its workflow branch is not merged."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import shlex
import subprocess
import sys
import time
import uuid

import yaml

ROOT = Path(__file__).resolve().parents[3]


def run(args: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    kwargs.setdefault('timeout', 60)
    return subprocess.run(args, text=True, check=True, capture_output=True, **kwargs)


def verify_context(name: str, context: Path) -> None:
    manifest = json.loads((ROOT / '.agents/evidence/verify/2026-11-25-engine-image-contexts.json').read_text())['templates'][name]
    actual = {str(p.relative_to(context)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(context.rglob('*')) if p.is_file()}
    expected = dict(manifest['source_files_sha256'])
    expected['Dockerfile'] = manifest['prepared_dockerfile_sha256']
    assert actual == expected, 'prepared image context differs from the repair PR'
    print('PASS exact repair context', name, manifest['source_context_sha256'], flush=True)


def verify_image(name: str, image: str, context: Path) -> None:
    verify_context(name, context)
    config = yaml.safe_load((ROOT / name / 'template.yaml').read_text())
    start = shlex.split(config['start_cmd'])
    ready = shlex.split(config['ready_cmd'])
    assert start and ready
    token = secrets.token_urlsafe(32)
    workspace = '/home/user/app'
    launch_env = {**os.environ, 'ABX_SERVER_TOKEN': token,
                  'ABX_SERVER_BASE_DIR': workspace, 'WORKSPACE': workspace}
    image_id = run(['docker', 'image', 'inspect', '--format', '{{.Id}}', image]).stdout.strip()
    print('Actual image', name, image_id, flush=True)
    ownership = uuid.uuid4().hex
    container_name = 'abx-engine-http-' + ownership
    try:
        container = run([
            'docker', 'create', '--init', '--name', container_name,
            '--label', 'abx.http-verification=' + ownership,
            '--publish', '127.0.0.1::9000',
            '--env', 'ABX_SERVER_TOKEN', '--env', 'ABX_SERVER_BASE_DIR', '--env', 'WORKSPACE',
            '--entrypoint', start[0], image, *start[1:],
        ], env=launch_env).stdout.strip()
        assert len(container) == 64 and all(c in '0123456789abcdef' for c in container)
        run(['docker', 'start', container])
        for attempt in range(60):
            health = subprocess.run(['docker', 'exec', container, *ready], text=True,
                                    capture_output=True, timeout=5)
            if health.returncode == 0:
                break
            time.sleep(0.5)
        else:
            raise AssertionError('manifest readiness command failed')

        identity = r'''
import hashlib, json, os, pathlib, subprocess, sys
assert os.geteuid() != 0
name = sys.argv[1]
expected = ({'postgresql-17':'17.11-0+deb13u1', 'postgresql-client-17':'17.11-0+deb13u1',
             'libpq5':'17.11-0+deb13u1', 'redis-server':'5:8.0.2-3+deb13u3',
             'redis-tools':'5:8.0.2-3+deb13u3'} if name == 'dev-services' else
            {'pandoc':'3.1.11.1+ds-2', 'pandoc-data':'3.1.11.1-3',
             'libreoffice-writer-nogui':'4:25.2.3-2+deb13u9',
             'libreoffice-core-nogui':'4:25.2.3-2+deb13u9',
             'libreoffice-common':'4:25.2.3-2+deb13u9'})
for package, version in expected.items():
    result = subprocess.check_output(['dpkg-query','-W','-f=${Version}',package],text=True)
    assert result == version, (package,result)
sources = pathlib.Path('/etc/apt/sources.list.d/debian.sources').read_text()
assert sources.count('20261112T000000Z') == 2 and sources.count('Signed-By:') == 2
assert sources.count('Check-Valid-Until: no') == 2 and 'mirrors.aliyun.com' not in sources
assert pathlib.Path('/usr/share/keyrings/debian-archive-keyring.pgp').is_file()
print('PASS actual non-root user, installed engines, archive sources and keyring')
root=pathlib.Path('/home/user/app')
print(json.dumps(sorted(p.name for p in root.iterdir() if p.name != '__pycache__')))
'''
        inspected = run(['docker', 'exec', container, 'python3', '-c', identity, name]).stdout
        print(inspected.splitlines()[0], flush=True)
        before = json.loads(inspected.splitlines()[-1])
        source = ROOT / name / 'commands.py'
        observed = run(['docker', 'exec', container, 'python3', '-c',
                        "from pathlib import Path; import hashlib; print(hashlib.sha256(Path('/home/user/app/commands.py').read_bytes()).hexdigest())"]).stdout.strip()
        assert observed == hashlib.sha256(source.read_bytes()).hexdigest()

        address = run(['docker', 'port', container, '9000/tcp']).stdout.strip()
        host, port = address.rsplit(':', 1)
        assert host == '127.0.0.1' and 0 < int(port) < 65536
        test_env = {key: os.environ[key] for key in ('PATH', 'LANG', 'LC_ALL', 'TMPDIR') if key in os.environ}
        test_env.update({'ABX_SERVER_TOKEN': token, 'E2E_BASE_URL': 'http://' + address,
                         'E2E_BASE_DIR': workspace, 'E2E_WORKSPACE': workspace,
                         'E2E_REQUIRE_DATABASES': '1', 'E2E_REQUIRE_DOCUMENT': '1'})
        subprocess.run([sys.executable, str(ROOT / name / 'e2e_test.py')],
                       cwd=ROOT / name, env=test_env, check=True, timeout=300)
        cleanup_check = r'''
import json, pathlib
root=pathlib.Path('/home/user/app')
print(json.dumps(sorted(p.name for p in root.iterdir() if p.name != '__pycache__')))
active=[]
for path in pathlib.Path('/proc').glob('[0-9]*/comm'):
    try:
        command=path.read_text().strip()
        if command in {'postgres','redis-server','soffice.bin','oosplash'}:
            active.append(command)
    except (FileNotFoundError,ProcessLookupError):
        pass
assert not active, active
'''
        after = json.loads(run(['docker', 'exec', container, 'python3', '-c', cleanup_check]).stdout)
        assert after == before, 'HTTP controller left workspace artifacts'
        print('PASS strict HTTP controller, unchanged workspace top-level entries and backend process-name absence', name, flush=True)
    finally:
        owned = subprocess.run(['docker', 'inspect', '--format', '{{json .Config.Labels}}', container_name],
                               text=True, capture_output=True, timeout=30)
        if owned.returncode == 0:
            labels = json.loads(owned.stdout)
            assert labels.get('abx.http-verification') == ownership, 'container ownership mismatch'
            run(['docker', 'rm', '--force', container_name])
        else:
            assert 'No such object' in owned.stderr or 'No such container' in owned.stderr
        absent = subprocess.run(['docker', 'inspect', container_name], text=True, capture_output=True, timeout=30)
        assert absent.returncode != 0 and ('No such object' in absent.stderr or 'No such container' in absent.stderr)
        print('PASS independent owned container absence', name, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--template', required=True, choices=['dev-services', 'document-tools'])
    parser.add_argument('--context', type=Path, required=True)
    args = parser.parse_args()
    verify_image(args.template, 'abx-l1:' + args.template, args.context)
