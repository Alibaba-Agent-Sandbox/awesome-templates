"""Genuine pinned Grok headless CLI with isolated native state and explicit BYOK."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import tempfile
import threading
from urllib.parse import urlsplit
from agent_sandbox.server import command, start

_ROOT = Path(os.environ.get('WORKSPACE','/home/user/workspace')).resolve()
_CONFIG = {name:os.environ.get('GROK_'+name,'').strip() for name in ['MODEL_API_KEY','MODEL_BASE_URL','MODEL']}
_NATIVE_SHA256 = '2a46d9e4d7ebd7a9cff7f95716714b19dad5f21dd2a497822400b1fb128969aa'
_LOCK = threading.Lock()
_SPEC = importlib.util.spec_from_file_location('grok_owned_process',Path(__file__).with_name('process.py'))
_PROCESS = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROCESS)


def _paths():
    native = Path('/opt/grok/bin/grok')
    if not native.is_file() or not os.access(native,os.X_OK) or not 0<native.stat().st_size<=256*1024*1024:
        raise RuntimeError('pinned Linuxx64 official Grok native distribution unavailable')
    with native.open('rb') as source:
        if hashlib.file_digest(source,'sha256').hexdigest()!=_NATIVE_SHA256:
            raise RuntimeError('actual native Grok binary differs from pinned1.0.62')
    return str(native)


def _validate_config():
    if not all(_CONFIG.values()):
        raise ValueError('GROK_MODEL_API_KEY, GROK_MODEL_BASE_URL and GROK_MODEL must be set before server startup')
    base,key,model = _CONFIG['MODEL_BASE_URL'],_CONFIG['MODEL_API_KEY'],_CONFIG['MODEL']
    if len(base)>2048 or any(c.isspace() or ord(c)<32 for c in base):
        raise ValueError('invalid bounded model base URL')
    try:
        value=urlsplit(base)
        value.port
    except ValueError:
        raise ValueError('invalid model base URL') from None
    if not value.hostname or value.username or value.password or value.query or value.fragment or (value.scheme!='https' and not(value.scheme=='http' and value.hostname in ['127.0.0.1','localhost','::1'])):
        raise ValueError('model base requires HTTPS or literal local HTTP without userinfo/query/fragment')
    if len(key)>8192 or any(c in key for c in '\r\n\0'):
        raise ValueError('invalid bounded model key')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}',model):
        raise ValueError('invalid bounded model identifier')


def _environment(root,*,model):
    env={name:os.environ[name] for name in ['SSL_CERT_FILE','SSL_CERT_DIR'] if name in os.environ}
    env.update(PATH='/opt/node/current/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin',
        HOME=str(root),TMPDIR=str(root),XDG_CACHE_HOME=str(root/'cache'),XDG_CONFIG_HOME=str(root/'config'),
        XDG_DATA_HOME=str(root/'xdg-data'),GROK_HOME=str(root/'.grok'),GROK_WORKFLOWS='0',GROK_MEMORY='0',
        GROK_TELEMETRY_ENABLED='0',GROK_TELEMETRY_TRACE_UPLOAD='0',NO_COLOR='1',TERM='dumb',LANG='C.UTF-8')
    if model:
        _validate_config();env['ABX_GROK_MODEL_KEY']=_CONFIG['MODEL_API_KEY']
    return env


def _profile(root,*,model):
    home=root/'.grok';home.mkdir(mode=0o700)
    value='[cli]\nauto_update = false\nuse_leader = false\n[features]\ntelemetry = false\n[telemetry]\ntrace_upload = false\n[memory]\nenabled = false\n[workflows]\nenabled = false\n[shell_environment_policy]\ninherit = "core"\nignore_default_excludes = false\n'
    if model:
        value+='[models]\ndefault = "abx-approved"\n[model.abx-approved]\nmodel = '+json.dumps(_CONFIG['MODEL'])+'\nbase_url = '+json.dumps(_CONFIG['MODEL_BASE_URL'])+'\nenv_key = "ABX_GROK_MODEL_KEY"\napi_backend = "chat_completions"\nmax_completion_tokens = 4096\ncontext_window = 65536\n'
    path=home/'config.toml'
    with path.open('x') as output:
        path.chmod(0o600);output.write(value)


def _run(args,*,cwd,timeout,model,prompt=None):
    if not _LOCK.acquire(blocking=False):
        raise RuntimeError('another Grok operation is active')
    try:
        cli=_paths()
        with tempfile.TemporaryDirectory(prefix='abx-grok-home-') as value:
            private=Path(value)
            private.chmod(0o700)
            env=_environment(private,model=model)
            _profile(private,model=model)
            argv=[cli,*args]
            if prompt is None:
                code,out,err=_PROCESS.run(argv,cwd=cwd,env=env,timeout=timeout)
            else:
                descriptor=os.memfd_create('grok-prompt',os.MFD_CLOEXEC)
                with os.fdopen(descriptor,'w+b') as source:
                    source.write(prompt.encode());source.seek(0)
                    code,out,err=_PROCESS.run(argv,cwd=cwd,env=env,timeout=timeout,input_file=source)
        for secret in [_CONFIG['MODEL_API_KEY'],_CONFIG['MODEL_BASE_URL']]:
            if secret:
                for encoded in {secret,json.dumps(secret,ensure_ascii=True)[1:-1],json.dumps(secret,ensure_ascii=False)[1:-1]}:
                    out=out.replace(encoded,'[REDACTED]');err=err.replace(encoded,'[REDACTED]')
        return {'stdout':out,'stderr':err,'exit_code':code,'native_version':'1.0.62'}
    finally:
        _LOCK.release()


@command('grok_version',description='Read actual pinned Grok1.0.62 version and native SHA256 without model/auth calls.')
def grok_version() -> dict:
    result=_run(['--version'],cwd=_ROOT,timeout=30,model=False)
    if result['exit_code']!=0 or result['stdout'].strip()!='grok 1.0.62 (1474f9cbdd91)':
        raise RuntimeError('actual Grok CLI version differs from1.0.62')
    return {'native_version':'1.0.62'}


@command('grok_setup_check',description='Read-only explicit compatible provider presence; no secret values or networking.')
def grok_setup_check() -> dict:
    return {'mode':'openai-compatible-byok','xai_account_required':False,
        'base_url_set':bool(_CONFIG['MODEL_BASE_URL']),'api_key_set':bool(_CONFIG['MODEL_API_KEY']),'model_set':bool(_CONFIG['MODEL'])}


@command('grok',description='Bounded genuine native headless act/yolo coding in a trusted disposable sandbox.')
def grok(prompt: str,cwd: str='',command_timeout: int=300) -> dict:
    if not isinstance(prompt,str) or not prompt.strip() or '\0'in prompt or len(prompt.encode())>32768:
        raise ValueError('prompt must contain1..32768UTF-8 bytes without NUL')
    if not isinstance(cwd,str) or len(cwd.encode())>4096 or '\0'in cwd:
        raise ValueError('invalid bounded cwd')
    if type(command_timeout)is not int or not 1<=command_timeout<=600:
        raise ValueError('command_timeout must be1..600seconds')
    directory=(_ROOT/cwd).resolve()
    if not directory.is_relative_to(_ROOT) or not directory.is_dir():
        raise ValueError('cwd must exist inside WORKSPACE')
    _validate_config()
    args=['--output-format','json','--always-approve','--no-plan','--no-subagents',
        '--disable-web-search','--sandbox','off','--model','abx-approved','--cwd',str(directory),
        '--max-turns','20','--tools','read_file,write_file,search_replace,grep,list_dir,run_terminal_cmd',
        '--disallowed-tools','Agent','--prompt-file','/dev/stdin']
    return _run(args,cwd=directory,timeout=command_timeout,model=True,prompt=prompt)


if __name__=='__main__':
    start(int(os.environ.get('ABX_SERVER_PORT','9000')))
