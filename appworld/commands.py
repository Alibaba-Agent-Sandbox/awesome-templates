"""Original AppWorld engine, private protected bundles and native score verification."""
import importlib.util,json,os,re,secrets,tempfile,threading
from pathlib import Path
from urllib.parse import urlsplit
from agent_sandbox.server import command,start

_ROOT=Path(os.environ.get('WORKSPACE','/home/user/workspace')).resolve()
_CONFIG={key:os.environ.get('APPWORLD_'+key,'').strip()for key in ['MODEL_API_KEY','MODEL_BASE_URL','MODEL']}
_LOCK=threading.Lock()
_SPEC=importlib.util.spec_from_file_location('appworld_owned_process',Path(__file__).with_name('process.py'))
_PROCESS=importlib.util.module_from_spec(_SPEC);_SPEC.loader.exec_module(_PROCESS)


def _config():
    if not all(_CONFIG.values()):raise ValueError('APPWORLD_MODEL_API_KEY, APPWORLD_MODEL_BASE_URL and APPWORLD_MODEL required before startup')
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
    env.update(PATH='/opt/appworld-venv/bin:/usr/local/bin:/usr/bin:/bin',HOME=str(private),TMPDIR=str(private),
        XDG_CACHE_HOME=str(private/'cache'),XDG_CONFIG_HOME=str(private/'config'),APPWORLD_ROOT=str(private/'world'),APPWORLD_CACHE=str(private/'cache'),NO_COLOR='1',LANG='C.UTF-8')
    return env


def _runtime():
    binary=Path('/opt/appworld-venv/bin/python')
    if not binary.is_file()or not os.access(binary,os.X_OK):raise RuntimeError('pinned AppWorld native environment unavailable')
    return str(binary),str(Path(__file__).with_name('worker.py'))


def _invoke(operation,data,timeout):
    if not _LOCK.acquire(blocking=False):raise RuntimeError('another AppWorld native operation is active')
    try:
        binary,worker=_runtime()
        raw=json.dumps(data,ensure_ascii=False).encode()
        if len(raw)>32768:raise ValueError('native request exceeds32KiB')
        with tempfile.TemporaryDirectory(prefix='abx-appworld-home-')as value:
            private=Path(value);private.chmod(0o700);descriptor=os.memfd_create('appworld-request',os.MFD_CLOEXEC)
            with os.fdopen(descriptor,'w+b')as source:
                source.write(raw);source.seek(0)
                code,out,err=_PROCESS.run([binary,worker,operation],
                    cwd=private,env=_environment(private),timeout=timeout,input_file=source)
        if code:
            detail=''
            try:
                diagnostic=json.loads(err.strip().splitlines()[-1])
                kind=diagnostic.get('error_type')
                stage=diagnostic.get('native_stage')
                if isinstance(kind,str)and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,63}',kind)and not any(secret and secret in kind for secret in _CONFIG.values())and stage in ['request','upstream','private_copy','installer','data_unpack','task','configuration','native_run','summary','artifact','replay']:
                    detail='; '+stage+' ('+kind+')'
                    bootstrap_kind=diagnostic.get('bootstrap_error_type')
                    if bootstrap_kind in ['ModuleNotFoundError','ImportError','PermissionError','FileNotFoundError','TypeError','AttributeError','RuntimeError','ValueError','NativeInstallerNonzero']:
                        detail+='; installer='+bootstrap_kind
                        missing=diagnostic.get('missing_module')
                        if isinstance(missing,str)and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.]{0,127}',missing)and not any(secret and secret in missing for secret in _CONFIG.values()):
                            detail+='; missing module '+missing
                    reason=diagnostic.get('native_termination')
                    if reason in ['max_steps','timeout','too_many_errors','agent_error','user_error','infrastructure_error','context_window_exceeded','unexpected_error']:
                        detail+='; termination='+reason
            except (ValueError,IndexError,TypeError):pass
            if not detail:
                classes=re.findall(r'^([A-Za-z_][A-Za-z0-9_]{0,63}(?:Error|Exception)):',err,re.M)
                if classes and not any(secret and secret in classes[-1]for secret in _CONFIG.values()):
                    detail='; entrypoint ('+classes[-1]+')'
                else:detail='; diagnostic_class_unavailable'
            detail+='; native_exit_code='+str(code)
            if operation=='version':
                try:
                    diagnostic=json.loads(err.strip().splitlines()[-1])
                    missing=diagnostic.get('missing_module','')
                    if diagnostic.get('error_type')=='ModuleNotFoundError'and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.]{0,127}',missing):
                        if not any(secret and secret in missing for secret in _CONFIG.values()):detail='; missing module '+missing
                except (ValueError,IndexError,TypeError):pass
            raise RuntimeError('native AppWorld operation failed; private diagnostics omitted'+detail)
        value=json.loads(out)
        if not isinstance(value,dict):raise RuntimeError('native result must be an object')
        for secret in [_CONFIG['MODEL_API_KEY'],_CONFIG['MODEL_BASE_URL']]:
            if secret and secret in json.dumps(value,ensure_ascii=False):raise RuntimeError('native result contained private configuration')
        return value
    finally:_LOCK.release()


def _task(task):
    if not isinstance(task,str) or not re.fullmatch(r'[A-Za-z0-9_-]{0,64}',task):
        raise ValueError('task must be empty or a bounded original training task ID')


@command('appworld_version',description='Verify installed native AppWorld package and original encrypted data/bundle provenance without model credentials.')
def appworld_version() -> dict:
    return _invoke('version',{},60)


@command('appworld_setup_check',description='Read-only explicit model configuration presence, without secret values or native setup.')
def appworld_setup_check() -> dict:
    return {'mode':'original-appworld-engine-authored-model-bridge',
            'base_url_set':bool(_CONFIG['MODEL_BASE_URL']),
            'api_key_set':bool(_CONFIG['MODEL_API_KEY']),
            'model_set':bool(_CONFIG['MODEL'])}


@command('appworld_native_smoke',description='Load an original training world, invoke its original API through native execute and clean private decrypted state.')
def appworld_native_smoke() -> str:
    value=_invoke('smoke',{},120)
    if value.get('native_version')!='0.1.3.post1' or value.get('original_engine') is not True or value.get('protected_state_private') is not True or type(value.get('native_api_calls')) is not int or value['native_api_calls']<=0:
        raise RuntimeError('original native AppWorld smoke incomplete')
    return 'original AppWorld0.1.3.post1 native API and private cleanup OK'


@command('appworld_run',description='Solve one original training task with an explicit compatible model, original native engine/evaluator and encrypted result bundle.')
def appworld_run(task: str='',max_steps: int=30,command_timeout: int=600) -> dict:
    _task(task)
    if type(max_steps) is not int or not 1<=max_steps<=40:
        raise ValueError('max_steps must be1..40')
    if type(command_timeout) is not int or not 30<=command_timeout<=900:
        raise ValueError('command_timeout must be30..900seconds')
    settings=_config()
    if not _ROOT.is_dir():
        raise ValueError('WORKSPACE must exist')
    folder=_ROOT/('abx_appworld_result_'+secrets.token_hex(16))
    folder.mkdir(mode=0o700)
    try:
        return _invoke('run',{'task':task,'max_steps':max_steps,'settings':settings,
                             'artifact':str(folder/'result.bundle')},command_timeout)
    except BaseException:
        import shutil
        shutil.rmtree(folder)
        raise


@command('appworld_verify_artifact',description='Independently reload an encrypted original task result and re-evaluate its saved databases with the native evaluator, without model credentials.')
def appworld_verify_artifact(path: str,task: str='') -> dict:
    _task(task)
    if not isinstance(path,str) or len(path.encode())>4096 or '\0' in path:
        raise ValueError('invalid bounded artifact path')
    target=(_ROOT/path).resolve()
    if not target.is_relative_to(_ROOT) or not target.is_file() or not 0<target.stat().st_size<=64*1024*1024:
        raise ValueError('artifact must be an existing bounded workspace file')
    return _invoke('verify',{'task':task,'artifact':str(target)},180)


if __name__=='__main__':
    start(int(os.environ.get('ABX_SERVER_PORT','9000')))
