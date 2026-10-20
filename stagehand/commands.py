"""Native Stagehand4 local browser actions with explicit private model transport."""
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import tempfile
import threading
from urllib.parse import urlsplit
from agent_sandbox.server import command, start

_HERE = Path(__file__).resolve().parent
_ROOT = Path(os.environ.get('WORKSPACE', '/home/user/app')).resolve()
_CONFIG = {key: os.environ.get('STAGEHAND_'+key, '').strip() for key in ['API_KEY', 'BASE_URL', 'MODEL']}
_LOCK = threading.Lock()
_SPEC = importlib.util.spec_from_file_location('stagehand_owned_process', _HERE/'process.py')
_PROCESS = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROCESS)


def _url(value, *, model=False):
    if not isinstance(value, str) or not value or len(value.encode()) > 8192 or any(c.isspace() or ord(c)<32 for c in value):
        raise ValueError('URL must be nonempty and bounded without whitespace/control characters')
    try:
        parsed = urlsplit(value)
        parsed.port
    except ValueError:
        raise ValueError('invalid URL') from None
    if parsed.scheme not in ['https', 'http'] or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('URL requires HTTP(S) without userinfo')
    if model and (parsed.query or parsed.fragment or (parsed.scheme == 'http' and parsed.hostname not in ['localhost','127.0.0.1','::1'])):
        raise ValueError('model URL requires HTTPS or literal local HTTP without query/fragment')
    return value


def _invoke(value=None):
    if not _LOCK.acquire(blocking=False):
        raise RuntimeError('another Stagehand operation is active')
    try:
        node = Path(os.environ.get('STAGEHAND_NODE', '/opt/node/current/bin/node'))
        if not node.is_file() or not os.access(node, os.X_OK):
            raise RuntimeError('pinned Node runtime unavailable')
        with tempfile.TemporaryDirectory(prefix='abx-stagehand-') as name:
            private = Path(name)
            private.chmod(0o700)
            env = {key:os.environ[key] for key in ['PATH','SSL_CERT_FILE','SSL_CERT_DIR','NODE_EXTRA_CA_CERTS'] if key in os.environ}
            env.update(HOME=name, LANG='C.UTF-8', XDG_CONFIG_HOME=str(private/'config'), XDG_CACHE_HOME=str(private/'cache'), TMPDIR=name)
            argv = [str(node), str(_HERE/'worker.mjs')]
            if value is None:
                argv.append('--version')
                code, output, _ = _PROCESS.run(argv, cwd=private, env=env, timeout=30)
                if code or output.strip() != '4.3.0':
                    raise RuntimeError('actual native Stagehand package differs from4.3.0')
                return output.strip()
            # Anonymous memory only: no credential value in a file, argv or browser env.
            fd = os.memfd_create('stagehand-request', os.MFD_CLOEXEC)
            with os.fdopen(fd, 'w+b') as source:
                source.write(json.dumps(value, ensure_ascii=False).encode())
                source.seek(0)
                code, output, _ = _PROCESS.run(argv, cwd=private, env=env, timeout=value.get('command_timeout',60), input_file=source)
        if code:
            raise RuntimeError('native Stagehand operation failed; private upstream diagnostics omitted')
        try:
            result = json.loads(output)
        except ValueError:
            raise RuntimeError('invalid native Stagehand result') from None
        def scrub(value):
            if isinstance(value,str):
                for secret in [_CONFIG['API_KEY'],_CONFIG['BASE_URL']]:
                    if secret:
                        value = value.replace(secret,'[REDACTED]')
                return value
            if isinstance(value,list):
                return [scrub(item) for item in value]
            if isinstance(value,dict):
                return {scrub(key):scrub(item) for key,item in value.items()}
            return value
        return scrub(result)
    finally:
        _LOCK.release()


def _browser():
    path = Path('/opt/playwright/chromium-1208/chrome-linux64/chrome')
    if not path.is_file() or not os.access(path, os.X_OK):
        raise RuntimeError('pinned Chromium1208 unavailable')
    return str(path)


@command('stagehand_version', description='Read the actual native SDK4.3.0 without browser/model calls.')
def stagehand_version() -> str:
    return _invoke()


@command('stagehand_setup_check', description='Read configuration presence only; no network or secret values.')
def stagehand_setup_check() -> dict:
    return {'compatibility_profile':'explicit-native-extension-id','mode':'local-browser-compatible-client-llm', 'browserbase_account_required':False,
            **{name.lower()+'_set':bool(value) for name,value in _CONFIG.items()}}


@command('stagehand_self_test', description='Actual offline native browser/extension navigation/title/PNG and owned cleanup.')
def stagehand_self_test() -> str:
    value = _invoke({'mode':'self-test', 'browser_binary':_browser()})
    if value.get('self_test') != 'STAGEHAND_NATIVE_OK' or value.get('png_bytes',0)<100:
        raise RuntimeError('native Stagehand self-test failed')
    return 'STAGEHAND_NATIVE_OK'


@command('stagehand', description='One native local-browser act, optional schema text extraction and fresh PNG artifact.')
def stagehand(task: str, url: str, extract_instruction: str='', command_timeout: int=180) -> dict:
    for name,value,required in [('task',task,True),('extract_instruction',extract_instruction,False)]:
        if not isinstance(value,str) or (required and not value.strip()) or '\0' in value or len(value.encode())>32768:
            raise ValueError(name+' must be at most32768UTF-8 bytes without NUL')
    if type(command_timeout) is not int or not 1<=command_timeout<=600:
        raise ValueError('command_timeout must be1..600seconds')
    _url(url)
    if not all(_CONFIG.values()):
        raise RuntimeError('STAGEHAND_API_KEY, STAGEHAND_BASE_URL and STAGEHAND_MODEL are required before server startup')
    _url(_CONFIG['BASE_URL'],model=True)
    if len(_CONFIG['API_KEY'])>8192 or any(c in _CONFIG['API_KEY'] for c in '\r\n\0') or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}',_CONFIG['MODEL']):
        raise ValueError('invalid bounded model configuration')
    if not _ROOT.is_dir():
        raise ValueError('WORKSPACE must be an existing directory')
    directory = _ROOT/'stagehand-artifacts'
    if directory.is_symlink():
        raise ValueError('artifact directory must not be a symlink')
    directory.mkdir(exist_ok=True)
    artifact = directory/(secrets.token_hex(16)+'.png')
    with artifact.open('xb'):
        pass
    try:
        value = _invoke({'mode':'act','task':task,'url':url,'extract_instruction':extract_instruction,
            'command_timeout':command_timeout,'browser_binary':_browser(),'screenshot_path':str(artifact),
            'api_key':_CONFIG['API_KEY'],'base_url':_CONFIG['BASE_URL'],'model':_CONFIG['MODEL']})
        if value.get('screenshot_path')!=str(artifact) or value.get('png_bytes')!=artifact.stat().st_size or not 100<=artifact.stat().st_size<=8*1024*1024 or not artifact.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'):
            raise RuntimeError('native screenshot artifact mismatch')
        return value
    except BaseException:
        artifact.unlink(missing_ok=True)
        raise


if __name__ == '__main__':
    start(int(os.environ.get('ABX_SERVER_PORT','9000')))
