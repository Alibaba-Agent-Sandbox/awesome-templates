"""Genuine pinned Cline headless CLI with isolated native state and explicit BYOK."""
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
_CONFIG = {name:os.environ.get('CLINE_'+name,'').strip() for name in ['MODEL_API_KEY','MODEL_BASE_URL','MODEL']}
_NATIVE_SHA256 = '1ff8841d17d4d83763134c193d414e4f7fcf2ef56af759e5ebbe96727fc2c8f7'
_LOCK = threading.Lock()
_SPEC = importlib.util.spec_from_file_location('cline_owned_process',Path(__file__).with_name('process.py'))
_PROCESS = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROCESS)


def _paths():
    native = Path('/opt/cline/node_modules/@cline/cli-linux-x64/bin/cline')
    cli = Path('/opt/cline/node_modules/.bin/cline')
    if not cli.is_file() or not os.access(cli,os.X_OK) or not native.is_file() or not 0<native.stat().st_size<=200*1024*1024:
        raise RuntimeError('pinned Linuxx64 Cline native distribution unavailable')
    with native.open('rb') as source:
        if hashlib.file_digest(source,'sha256').hexdigest()!=_NATIVE_SHA256:
            raise RuntimeError('actual native Cline binary differs from pinned3.0.73')
    return str(cli)


def _validate_config():
    if not all(_CONFIG.values()):
        raise ValueError('CLINE_MODEL_API_KEY, CLINE_MODEL_BASE_URL and CLINE_MODEL must be set before server startup')
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
    env={name:os.environ[name] for name in ['SSL_CERT_FILE','SSL_CERT_DIR','NODE_EXTRA_CA_CERTS'] if name in os.environ}
    env.update(PATH='/opt/node/current/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin',
        HOME=str(root),TMPDIR=str(root),XDG_CACHE_HOME=str(root/'cache'),XDG_CONFIG_HOME=str(root/'config'),
        XDG_DATA_HOME=str(root/'xdg-data'),CLINE_DATA_DIR=str(root/'data'),CLINE_SANDBOX_DATA_DIR=str(root/'data'),CLINE_TEAM_DATA_DIR=str(root/'teams'),CLINE_SANDBOX='1',
        CLINE_PROVIDER_SETTINGS_PATH=str(root/'data/settings/providers.json'),CLINE_GLOBAL_SETTINGS_PATH=str(root/'global.json'),
        CLINE_MCP_SETTINGS_PATH=str(root/'mcp.json'),CLINE_LOG_ENABLED='0',CLINE_LOG_LEVEL='silent',NO_COLOR='1',TERM='dumb',LANG='C.UTF-8')
    if model:
        _validate_config()
        env['OPENAI_API_KEY']=_CONFIG['MODEL_API_KEY']
    return env


def _profile(root,*,model):
    globals_={'telemetryOptOut':True,'autoUpdateEnabled':False,'compactionEnabled':False,'tools':{'web_search':{'enabled':False}}}
    state={'version':1,'modes':{},'providers':{}}
    if model:
        state.update(lastUsedProvider='openai-compatible',providers={'openai-compatible':{'settings':{
            'provider':'openai-compatible','client':'openai-compatible','protocol':'openai-chat','model':_CONFIG['MODEL'],
            'baseUrl':_CONFIG['MODEL_BASE_URL'],'maxTokens':4096,'contextWindow':65536,'timeout':60000,
            'modelCatalog':{'loadLatestOnInit':False,'includeClineCloudModels':False,'loadPrivateOnAuth':False}},
            'updatedAt':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'tokenSource':'manual'}})
    # Native --data-dir rewrites the provider path before creating its manager.
    (root/'data/settings').mkdir(parents=True,mode=0o700)
    for filename,value in [('global.json',globals_),('data/settings/providers.json',state),('mcp.json',{'mcpServers':{}})]:
        path=root/filename
        with path.open('x') as output:
            path.chmod(0o600)
            json.dump(value,output)


def _run(args,*,cwd,timeout,model,prompt=None):
    if not _LOCK.acquire(blocking=False):
        raise RuntimeError('another Cline operation is active')
    try:
        cli=_paths()
        with tempfile.TemporaryDirectory(prefix='abx-cline-home-') as value:
            private=Path(value)
            private.chmod(0o700)
            env=_environment(private,model=model)
            _profile(private,model=model)
            argv=[cli,*args,'--config',str(private/'.cline'),'--data-dir',str(private/'data')]
            if prompt is None:
                code,out,err=_PROCESS.run(argv,cwd=cwd,env=env,timeout=timeout)
            else:
                descriptor=os.memfd_create('cline-prompt',os.MFD_CLOEXEC)
                with os.fdopen(descriptor,'w+b') as source:
                    source.write(prompt.encode());source.seek(0)
                    code,out,err=_PROCESS.run(argv,cwd=cwd,env=env,timeout=timeout,input_file=source)
        for secret in [_CONFIG['MODEL_API_KEY'],_CONFIG['MODEL_BASE_URL']]:
            if secret:
                for encoded in {secret,json.dumps(secret,ensure_ascii=True)[1:-1],json.dumps(secret,ensure_ascii=False)[1:-1]}:
                    out=out.replace(encoded,'[REDACTED]');err=err.replace(encoded,'[REDACTED]')
        return {'stdout':out,'stderr':err,'exit_code':code,'native_version':'3.0.73'}
    finally:
        _LOCK.release()


@command('cline_version',description='Read actual pinned Cline3.0.73 version and native SHA256 without model/auth calls.')
def cline_version() -> dict:
    result=_run(['--version'],cwd=_ROOT,timeout=30,model=False)
    if result['exit_code']!=0 or result['stdout'].strip()!='3.0.73':
        raise RuntimeError('actual Cline CLI version differs from3.0.73')
    return {'native_version':'3.0.73'}


@command('cline_setup_check',description='Read-only explicit compatible provider presence; no secret values or networking.')
def cline_setup_check() -> dict:
    return {'mode':'openai-compatible-byok','cline_account_required':False,
        'base_url_set':bool(_CONFIG['MODEL_BASE_URL']),'api_key_set':bool(_CONFIG['MODEL_API_KEY']),'model_set':bool(_CONFIG['MODEL'])}


@command('cline',description='Bounded genuine native headless act/yolo coding in a trusted disposable sandbox.')
def cline(prompt: str,cwd: str='',command_timeout: int=300) -> dict:
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
    args=['--json','--yolo','--provider','openai-compatible','--model',_CONFIG['MODEL'],'--cwd',str(directory),
        '--compaction','off','--retries','2','--timeout',str(command_timeout),
        'Complete the task provided on standard input.']
    return _run(args,cwd=directory,timeout=command_timeout,model=True,prompt=prompt)


if __name__=='__main__':
    start(int(os.environ.get('ABX_SERVER_PORT','9000')))
