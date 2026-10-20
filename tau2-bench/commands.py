"""Pinned original Tau2 retail runner with private model state and native replay."""
import importlib.util,json,os,re,secrets,tempfile,threading
from pathlib import Path
from urllib.parse import urlsplit
from agent_sandbox.server import command,start

_ROOT=Path(os.environ.get('WORKSPACE','/home/user/workspace')).resolve()
_CONFIG={key:os.environ.get('TAU2_'+key,'').strip()for key in ['MODEL_API_KEY','MODEL_BASE_URL','MODEL']}
_LOCK=threading.Lock()
_SPEC=importlib.util.spec_from_file_location('tau2_owned_process',Path(__file__).with_name('process.py'))
_PROCESS=importlib.util.module_from_spec(_SPEC);_SPEC.loader.exec_module(_PROCESS)


def _config():
    if not all(_CONFIG.values()):raise ValueError('TAU2_MODEL_API_KEY, TAU2_MODEL_BASE_URL and TAU2_MODEL required before startup')
    base,key,model=_CONFIG['MODEL_BASE_URL'],_CONFIG['MODEL_API_KEY'],_CONFIG['MODEL']
    if len(base)>2048 or any(c.isspace()or ord(c)<32 for c in base):raise ValueError('invalid model base')
    value=urlsplit(base)
    try:value.port
    except ValueError:raise ValueError('invalid model base port')from None
    if not value.hostname or value.username is not None or value.password is not None or value.query or value.fragment or(value.scheme!='https'and not(value.scheme=='http'and value.hostname in ['127.0.0.1','localhost','::1'])):raise ValueError('explicit HTTPS model base or literal local HTTP required')
    if len(key)>8192 or any(c in key for c in '\r\n\0'):raise ValueError('invalid bounded model key')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}',model):raise ValueError('invalid bounded model identifier')
    return {'key':key,'base':base,'model':model}


def _environment(private):
    env={key:os.environ[key]for key in ['SSL_CERT_FILE','SSL_CERT_DIR']if key in os.environ}
    env.update(PATH='/opt/tau2-venv/bin:/usr/local/bin:/usr/bin:/bin',HOME=str(private),TMPDIR=str(private),
        XDG_CACHE_HOME=str(private/'cache'),XDG_CONFIG_HOME=str(private/'config'),PYTHONPATH='/opt/tau2/src',
        TAU2_DATA_DIR='/opt/tau2/data',LITELLM_LOCAL_MODEL_COST_MAP='True',NO_COLOR='1',LANG='C.UTF-8')
    return env


def _runtime():
    binary=Path('/opt/tau2-venv/bin/python')
    if not binary.is_file()or not os.access(binary,os.X_OK):raise RuntimeError('pinned Tau2 native environment unavailable')
    return str(binary),str(Path(__file__).with_name('worker.py'))


def _invoke(operation,data,timeout):
    if not _LOCK.acquire(blocking=False):raise RuntimeError('another Tau2 native operation is active')
    try:
        binary,worker=_runtime()
        raw=json.dumps(data,ensure_ascii=False).encode()
        if len(raw)>32768:raise ValueError('native request exceeds32KiB')
        with tempfile.TemporaryDirectory(prefix='abx-tau2-home-')as value:
            private=Path(value);private.chmod(0o700);descriptor=os.memfd_create('tau2-request',os.MFD_CLOEXEC)
            with os.fdopen(descriptor,'w+b')as source:
                source.write(raw);source.seek(0)
                code,out,err=_PROCESS.run([binary,worker,operation],
                    cwd=private,env=_environment(private),timeout=timeout,input_file=source)
        if code:raise RuntimeError('native Tau2 operation failed; private diagnostics omitted')
        value=json.loads(out)
        if not isinstance(value,dict):raise RuntimeError('native result must be an object')
        for secret in [_CONFIG['MODEL_API_KEY'],_CONFIG['MODEL_BASE_URL']]:
            if secret and secret in json.dumps(value,ensure_ascii=False):raise RuntimeError('native result contained private configuration')
        return value
    finally:_LOCK.release()


def _task(domain,task_id):
    if domain!='retail':raise ValueError('only the reviewed retail text domain is supported')
    if not isinstance(task_id,str)or not re.fullmatch(r'[0-9]{1,3}',task_id):raise ValueError('task_id must be a native decimal retail ID')


@command('tau2_version',description='Inspect actual pinned upstream source/domain without model credentials.')
def tau2_version() -> dict:
    return _invoke('version',{},60)


@command('tau2_setup_check',description='Read-only model configuration presence without secret values or networking.')
def tau2_setup_check() -> dict:
    return {'mode':'native-retail-agent-and-user','base_url_set':bool(_CONFIG['MODEL_BASE_URL']),
        'api_key_set':bool(_CONFIG['MODEL_API_KEY']),'model_set':bool(_CONFIG['MODEL'])}


@command('tau2_run',description='Run one original retail task with real agent/user models and save a sanitized native trajectory.')
def tau2_run(domain: str='retail',task_id: str='0',max_steps: int=30,command_timeout: int=600) -> dict:
    _task(domain,task_id)
    if type(max_steps)is not int or not 5<=max_steps<=60:raise ValueError('max_steps must be5..60')
    if type(command_timeout)is not int or not 30<=command_timeout<=900:raise ValueError('command_timeout must be30..900seconds')
    settings=_config()
    if not _ROOT.is_dir():raise ValueError('WORKSPACE must exist')
    folder=_ROOT/('abx_tau2_result_'+secrets.token_hex(16));folder.mkdir(mode=0o700)
    try:return _invoke('run',{'task_id':task_id,'max_steps':max_steps,'settings':settings,'artifact':str(folder/'trajectory.json')},command_timeout)
    except BaseException:
        import shutil
        shutil.rmtree(folder)
        raise


@command('tau2_verify_artifact',description='Independently strict-replay one bounded native retail trajectory without model credentials.')
def tau2_verify_artifact(path: str,task_id: str='0') -> dict:
    _task('retail',task_id)
    if not isinstance(path,str)or len(path.encode())>4096 or'\0'in path:raise ValueError('invalid bounded trajectory path')
    target=(_ROOT/path).resolve()
    if not target.is_relative_to(_ROOT)or not target.is_file()or not 0<target.stat().st_size<=8*1024*1024:raise ValueError('trajectory must be an existing bounded workspace file')
    return _invoke('verify',{'task_id':task_id,'artifact':str(target)},120)


if __name__=='__main__':start(int(os.environ.get('ABX_SERVER_PORT','9000')))
