"""One audited real SWE-bench instance, genuine mini CLI, independent evaluation."""
from __future__ import annotations
import contextlib
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import sys
import tarfile
import tempfile
import uuid
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit
from agent_sandbox.server import command, start

HERE = Path(__file__).resolve().parent
run = runpy.run_path(str(HERE / 'swe_process.py'))['run']
MANIFEST = json.loads((HERE / 'instance.json').read_text())
RUNTIME = Path(os.environ.get('SWE_RUNTIME_DIR', '/opt/swe'))
ARCHIVE = RUNTIME / 'flask_base.tar.gz'
EVAL_ENV = Path('/opt/swe-eval') if RUNTIME == Path('/opt/swe') else RUNTIME / 'eval'
MINI = '/usr/local/bin/mini' if RUNTIME == Path('/opt/swe') else str(RUNTIME / 'agent/bin/mini')
AGENT_PYTHON = '/opt/swe-agent/bin/python' if RUNTIME == Path('/opt/swe') else str(RUNTIME / 'agent/bin/python')
GIT = '/usr/bin/git'


def _environment():
    env = {k: os.environ[k] for k in ('HOME', 'LANG', 'LC_ALL') if k in os.environ}
    env.update(PATH='/usr/local/bin:/usr/bin:/bin', PYTHON_DOTENV_DISABLED='1',
               GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_TERMINAL_PROMPT='0', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
    return env


def _checked(argv, *, cwd, timeout=120, env=None, input_text=None):
    code, out, _ = run(argv, cwd=str(cwd), env=env or _environment(), timeout=timeout, input_text=input_text)
    if code:
        raise RuntimeError(f'owned subprocess failed (exit {code}); output omitted')
    return out


def _root():
    workspace = Path(os.environ.get('WORKSPACE', '/home/user/app')).resolve()
    root = workspace / '.swe-runs'
    if root.is_symlink():
        raise RuntimeError('run storage must not be a symlink')
    root.mkdir(mode=0o700, exist_ok=True)
    return root


def _resolve(run_id):
    if not isinstance(run_id, str) or not re.fullmatch(r'[0-9a-f]{32}', run_id):
        raise ValueError('run_id must be the opaque ID returned by swe_prepare')
    root = _root(); target = root / run_id
    if target.is_symlink() or not target.is_dir() or target.resolve().parent != root:
        raise ValueError('unknown owned run_id')
    return target


@contextlib.contextmanager
def _locked(run_id):
    target = _resolve(run_id)
    lock = target / 'operation.lock'
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('another operation owns this run') from None
        yield target
    finally:
        os.close(fd)


def _checkout(target):
    blob = ARCHIVE.read_bytes()
    if hashlib.sha256(blob).hexdigest() != MANIFEST['archive_sha256']:
        raise RuntimeError('pinned upstream archive checksum mismatch')
    target.mkdir(mode=0o700)
    with tarfile.open(fileobj=io.BytesIO(blob)) as archive:
        for member in archive.getmembers():
            parts = Path(member.name).parts[1:]
            if not parts:
                continue
            if member.issym() or member.islnk() or member.isdev() or '..' in parts:
                raise RuntimeError('unsupported upstream archive member')
            destination = target.joinpath(*parts)
            if member.isdir():
                destination.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(archive.extractfile(member).read())
    _checked([GIT, 'init', '-q'], cwd=target)
    _checked([GIT, 'apply', '-'], cwd=target, input_text=MANIFEST['test_patch'])
    _checked([GIT, 'add', '.'], cwd=target)
    _checked([GIT, '-c', 'user.name=SWE slice', '-c', 'user.email=swe@example.invalid',
              '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'Pinned base and original benchmark test patch'], cwd=target)


def _test_results(xml_path):
    root = ET.parse(xml_path).getroot()
    cases = root.findall('.//testcase')
    expected = set(MANIFEST['fail_to_pass'] + MANIFEST['pass_to_pass'])
    seen = {}
    for case in cases:
        name = case.get('classname', '').replace('.', '/') + '.py::' + case.get('name', '')
        if name in seen or name not in expected:
            raise RuntimeError('unexpected or duplicate evaluation test identity')
        seen[name] = 'failed' if case.find('failure') is not None else ('error' if case.find('error') is not None else
                     ('skipped' if case.find('skipped') is not None else 'passed'))
    if set(seen) != expected:
        raise RuntimeError('evaluation did not execute every declared test')
    return seen


def _evaluate(target, patch=''):
    with tempfile.TemporaryDirectory(prefix='evaluate-', dir=target) as temporary:
        stage = Path(temporary); repo = stage / 'repo'; _checkout(repo)
        if patch:
            _checked([GIT, 'apply', '--check', '-'], cwd=repo, input_text=patch)
            _checked([GIT, 'apply', '-'], cwd=repo, input_text=patch)
        venv = stage / 'venv'; shutil.copytree(EVAL_ENV, venv, symlinks=True)
        env = _environment() | {'PYTHONPATH': str(repo / 'src'), 'PATH': str(venv / 'bin') + ':/usr/bin:/bin'}
        xml = stage / 'tests.xml'
        argv = [str(venv / 'bin/python'), '-m', 'pytest', '-q', '--junitxml', str(xml)] + MANIFEST['fail_to_pass'] + MANIFEST['pass_to_pass']
        code, _, _ = run(argv, cwd=str(repo), env=env, timeout=120)
        if code not in (0, 1):
            raise RuntimeError('evaluation collection/runtime failed; no score produced')
        states = _test_results(xml)
        ftp = {name: states[name] for name in MANIFEST['fail_to_pass']}
        ptp = {name: states[name] for name in MANIFEST['pass_to_pass']}
        return {'fail_to_pass': ftp, 'pass_to_pass': ptp,
                'passed': sum(s == 'passed' for s in states.values()),
                'failed': sum(s == 'failed' for s in states.values()),
                'errors': sum(s == 'error' for s in states.values()),
                'skipped': sum(s == 'skipped' for s in states.values()),
                'resolved_slice': code == 0 and all(s == 'passed' for s in states.values()),
                'official_benchmark_score': False, 'python': sys.version.split()[0]}


@command('swe_version', description='Pinned mini-SWE-agent distribution version, no model call.')
def swe_version() -> str:
    with tempfile.TemporaryDirectory(prefix='swe-version-') as temporary:
        env = _environment() | {'MSWEA_GLOBAL_CONFIG_DIR': temporary,
            'MSWEA_CONFIGURED': 'true', 'MSWEA_SILENT_STARTUP': '1'}
        _checked([MINI, '--help'], cwd=HERE, env=env)
        version = _checked([AGENT_PYTHON, '-c',
            'import importlib.metadata; print(importlib.metadata.version("mini-swe-agent"))'],
            cwd=HERE, env=env).strip()
        if version != '2.4.6':
            raise RuntimeError('unexpected mini-SWE-agent distribution version')
        return 'mini-swe-agent ' + version


@command('swe_setup_check', description='Inspect target model/runtime availability without exposing values.')
def swe_setup_check() -> dict:
    return {'api_key_set': bool(os.environ.get('SWE_API_KEY')),
            'base_url_set': bool(os.environ.get('SWE_BASE_URL')),
            'model_set': bool(os.environ.get('SWE_MODEL')),
            'runtime_available': Path(MINI).is_file() and ARCHIVE.is_file() and EVAL_ENV.is_dir()}


def _valid_baseline(baseline):
    return (baseline['failed'] == 1 and baseline['passed'] == 59 and not baseline['errors'] and not baseline['skipped']
            and baseline['fail_to_pass'] == dict.fromkeys(MANIFEST['fail_to_pass'], 'failed')
            and baseline['pass_to_pass'] == dict.fromkeys(MANIFEST['pass_to_pass'], 'passed'))


@command('swe_prepare', description='Prepare the one pinned real instance and verify its failing baseline.')
def swe_prepare(instance_id: str = MANIFEST['instance_id']) -> dict:
    if instance_id != MANIFEST['instance_id']:
        raise ValueError('this slice supports only the pinned manifest instance')
    run_id = uuid.uuid4().hex; target = _root() / run_id; target.mkdir(mode=0o700)
    try:
        _checkout(target / 'repo')
        shutil.copytree(EVAL_ENV, target / 'venv', symlinks=True)
        baseline = _evaluate(target)
        if not _valid_baseline(baseline):
            raise RuntimeError('baseline must reproduce exactly 1 failure and 59 passes')
        result = {'run_id': run_id, 'instance_id': instance_id, 'baseline': baseline}
        (target / 'baseline.json').write_text(json.dumps(result, indent=2))
        return result
    except BaseException:
        shutil.rmtree(target); raise


@command('swe_run_agent', description='Explicitly authorize genuine mini CLI shell actions in an owned sandbox.')
def swe_run_agent(run_id: str, allow_execution: bool = False, max_steps: int = 12,
                  command_timeout: int = 300) -> dict:
    if not isinstance(allow_execution, bool) or not allow_execution:
        raise ValueError('allow_execution=true is required for model-generated shell execution')
    if type(max_steps) is not int or not 1 <= max_steps <= 30:
        raise ValueError('max_steps must be an integer from 1 to 30')
    if type(command_timeout) is not int or not 30 <= command_timeout <= 900:
        raise ValueError('command_timeout must be an integer from 30 to 900')
    key = os.environ.get('SWE_API_KEY', ''); base = os.environ.get('SWE_BASE_URL', ''); model = os.environ.get('SWE_MODEL', '')
    parsed = urlsplit(base)
    if not key or not model or parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise RuntimeError('required model settings must be configured on this server process')
    with _locked(run_id) as target:
        with tempfile.TemporaryDirectory(prefix='agent-', dir=target) as temporary:
            private = Path(temporary); private.chmod(0o700)
            trajectory = private / 'trajectory.json'
            config = {'run': {'task': MANIFEST['problem_statement'] + '\nOnly change src/flask/blueprints.py. Preserve tests. Submit after checking the fix.'},
                'agent': {'agent_class': 'default', 'step_limit': max_steps, 'cost_limit': 0,
                          'wall_time_limit_seconds': command_timeout, 'output_path': str(trajectory)},
                'model': {'model_class': 'litellm_textbased', 'model_name': 'openai/' + model,
                          'cost_tracking': 'ignore_errors', 'model_kwargs': {'api_base': base, 'temperature': 0}},
                'environment': {'environment_class': 'swe_environment.OwnedLocalEnvironment',
                    'cwd': str(target / 'repo'), 'timeout': 30, 'env': {
                        'PATH': str(target / 'venv/bin') + ':/usr/local/bin:/usr/bin:/bin',
                        'PYTHONPATH': str(target / 'repo/src'), 'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1',
                        'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull}}}
            config_path = private / 'config.yaml'; config_path.write_text(json.dumps(config)); config_path.chmod(0o600)
            env = _environment() | {'OPENAI_API_KEY': key, 'MSWEA_GLOBAL_CONFIG_DIR': str(private / 'config'),
                'MSWEA_CONFIGURED': 'true', 'MSWEA_SILENT_STARTUP': '1', 'LITELLM_LOCAL_MODEL_COST_MAP': 'True',
                'PYTHONPATH': str(HERE)}
            builtin = _checked([AGENT_PYTHON, '-c', 'import importlib.util; from pathlib import Path; print(Path(importlib.util.find_spec("minisweagent").origin).parent / "config/default.yaml")'], cwd=HERE, env=env).strip()
            _checked([MINI, '-c', builtin, '-c', str(config_path), '-o', str(trajectory)],
                     cwd=target / 'repo', timeout=command_timeout, env=env)
            state = json.loads(trajectory.read_text())['info']
            result = {'run_id': run_id, 'exit_status': state.get('exit_status'),
                      'model_calls': state.get('model_stats', {}).get('api_calls', 0)}
            if result['exit_status'] != 'Submitted' or result['model_calls'] < 1:
                raise RuntimeError('mini did not submit a real model run')
            (target / 'agent.json').write_text(json.dumps(result))
            return result


def _patch(target):
    repo = target / 'repo'; path = repo / MANIFEST['allowed_source']
    if any(p.is_symlink() for p in [path, path.parent, path.parent.parent]) or not path.is_file() or path.stat().st_size > 512000:
        raise RuntimeError('supported source must remain a regular bounded file')
    patch = _checked([GIT, '-c', 'core.hooksPath=/dev/null', 'diff', '--no-ext-diff', '--no-textconv', 'HEAD', '--', MANIFEST['allowed_source']], cwd=repo)
    if not patch:
        raise RuntimeError('no supported source edit; no score produced')
    for name, value in os.environ.items():
        if value and any(word in name.upper() for word in ('KEY', 'TOKEN', 'SECRET', 'PASSWORD', 'CREDENTIAL')):
            if any(variant in patch for variant in (value, json.dumps(value)[1:-1])):
                raise RuntimeError('submission contains configured secret material; artifact refused')
    return patch


@command('swe_evaluate', description='Apply only the supported source diff to fresh base/test copies and run all 60 nodes.')
def swe_evaluate(run_id: str) -> dict:
    with _locked(run_id) as target:
        patch = _patch(target); result = _evaluate(target, patch)
        (target / 'submission.patch').write_text(patch)
        (target / 'report.json').write_text(json.dumps(result, indent=2))
        return result | {'run_id': run_id, 'patch_path': str(target / 'submission.patch'), 'report_path': str(target / 'report.json')}


@command('swe_report', description='Return the sanitized persisted evaluation and artifact paths.')
def swe_report(run_id: str) -> dict:
    with _locked(run_id) as target:
        path = target / 'report.json'
        if not path.is_file():
            raise ValueError('run swe_evaluate first')
        return json.loads(path.read_text()) | {'run_id': run_id, 'patch_path': str(target / 'submission.patch'), 'report_path': str(path)}


@command('swe_cleanup', description='Remove only the owned run directory after other operations finish.')
def swe_cleanup(run_id: str) -> bool:
    with _locked(run_id) as target:
        shutil.rmtree(target)
    return True


if __name__ == '__main__':
    start(int(os.environ.get('ABX_SERVER_PORT', '9000')))
