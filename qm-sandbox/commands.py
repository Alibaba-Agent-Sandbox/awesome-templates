"""Original QM native APIs and original Agent Sandbox SDK, with owned lifecycle."""
import importlib.util,json,os,re,tempfile,threading
from pathlib import Path
from urllib.parse import urlsplit
from agent_sandbox.server import command,start

ROOT=Path(os.environ.get('WORKSPACE','/home/user/app')).resolve()
MODEL={name:os.environ.get('QM_'+name,'').strip()for name in ['MODEL_API_KEY','MODEL_BASE_URL','MODEL']}
SDK_BASE=os.environ.get('QM_SANDBOX_BASE_URL','http://127.0.0.1:9000').strip()
SDK_TOKEN=os.environ.get('QM_SANDBOX_TOKEN')or os.environ.get('ABX_SERVER_TOKEN','')
LOCK=threading.Lock()
spec=importlib.util.spec_from_file_location('qm_owned_process',Path(__file__).with_name('process.py'))
PROCESS=importlib.util.module_from_spec(spec);spec.loader.exec_module(PROCESS)


def sdk_settings():
    value=urlsplit(SDK_BASE)
    try:value.port
    except ValueError:raise ValueError('invalid SDK base port')from None
    if value.scheme!='http'or value.hostname not in ['127.0.0.1','::1']or value.username is not None or value.password is not None or value.query or value.fragment or value.path not in ['', '/']:
        raise ValueError('explicit literal-loopback SDK base required')
    if len(SDK_TOKEN)>8192 or any(char in SDK_TOKEN for char in '\r\n\0'):raise ValueError('invalid bounded SDK token')
    return {'sdk_base':SDK_BASE,'sdk_token':SDK_TOKEN}


def model_settings():
    if not all(MODEL.values()):raise ValueError('QM_MODEL_API_KEY, QM_MODEL_BASE_URL and QM_MODEL required before server startup')
    base,key,model=MODEL['MODEL_BASE_URL'],MODEL['MODEL_API_KEY'],MODEL['MODEL']
    if len(base)>2048 or any(char.isspace()or ord(char)<32 for char in base):raise ValueError('invalid bounded model base')
    value=urlsplit(base)
    try:value.port
    except ValueError:raise ValueError('invalid model base port')from None
    if not value.hostname or value.username is not None or value.password is not None or value.query or value.fragment or(value.scheme!='https'and not(value.scheme=='http'and value.hostname in ['127.0.0.1','::1','localhost'])):raise ValueError('explicit HTTPS model base or literal local HTTP required')
    if len(key)>8192 or any(ord(char)<32 for char in key):raise ValueError('invalid bounded model key')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}',model):raise ValueError('invalid model identifier')
    return {'base':base,'key':key,'model':model}


def workspace(cwd):
    if not isinstance(cwd,str)or len(cwd.encode())>4096 or '\0'in cwd:raise ValueError('invalid bounded cwd')
    path=(ROOT/cwd).resolve()
    if not path.is_relative_to(ROOT)or not path.is_dir():raise ValueError('cwd must be existing directory inside WORKSPACE')
    return str(path)


def redact(value):
    if isinstance(value,str):
        for secret in [MODEL['MODEL_API_KEY'],MODEL['MODEL_BASE_URL'],SDK_TOKEN,SDK_BASE]:
            if secret:
                for text in {secret,json.dumps(secret)[1:-1],json.dumps(secret,ensure_ascii=False)[1:-1]}:value=value.replace(text,'[REDACTED]')
        return value
    if isinstance(value,dict):return {key:redact(item)for key,item in value.items()}
    if isinstance(value,list):return [redact(item)for item in value]
    return value


def environment(private):
    env={name:os.environ[name]for name in ['SSL_CERT_FILE','SSL_CERT_DIR']if name in os.environ}
    env.update(PATH='/opt/node/current/bin:/usr/local/bin:/usr/bin:/bin',HOME=str(private),TMPDIR=str(private),
        XDG_CACHE_HOME=str(private/'cache'),XDG_CONFIG_HOME=str(private/'config'),
        LANG='C.UTF-8',NO_COLOR='1',TERM='dumb',NODE_OPTIONS='--use-system-ca',
        GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null')
    return env


def runtime():
    binary=Path('/opt/node/current/bin/node')
    if not binary.is_file()or not os.access(binary,os.X_OK):raise RuntimeError('original pinned QM Node runtime unavailable')
    return str(binary),str(Path(__file__).with_name('worker.mjs'))


# Generated from scripts/process_runners/qm_invoke.py; update with scripts/sync_process_runners.py.
def invoke(operation,data,timeout):
    if not LOCK.acquire(blocking=False):raise RuntimeError('another original QM operation is active')
    try:
        binary,worker=runtime()
        raw=json.dumps(data,ensure_ascii=False).encode()
        if len(raw)>262144:raise ValueError('native request exceeds256KiB')
        with tempfile.TemporaryDirectory(prefix='abx-qm-home-')as value:
            private=Path(value);private.chmod(0o700)
            descriptor=os.memfd_create('qm-native-request',os.MFD_CLOEXEC)
            with os.fdopen(descriptor,'w+b')as source:
                source.write(raw);source.seek(0)
                code,out,err=PROCESS.run([binary,worker,operation],cwd=private,env=environment(private),timeout=timeout,input_file=source)
        try:value=json.loads(out)
        except ValueError:raise RuntimeError('original QM native result protocol invalid; raw output omitted')from None
        if code:
            if not isinstance(value,dict):value={}
            kind=value.get('error_type')
            if not isinstance(kind,str)or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,63}',kind):kind='NativeFailure'
            detail=''
            stage=value.get('native_stage')
            if stage in ['request','metadata','sdk_import','qm_tools_import','qm_harness_import','qm_workspace_import','qm_acl_import','qm_provider_import','identity','sdk_provision','sdk_roundtrip','provider_configuration','harness_setup','harness_run']:
                detail+='; stage='+stage
            native_code=value.get('error_code')
            if isinstance(native_code,str)and re.fullmatch(r'[A-Z][A-Z0-9_]{0,79}',native_code):detail+='; native_code='+native_code
            missing=value.get('missing_module')
            if isinstance(missing,str)and re.fullmatch(r'[@A-Za-z0-9_./-]{1,128}',missing):detail+='; missing_module='+missing
            counts=value.get('native_counters')
            if isinstance(counts,dict):
                for name in ['model_requests','native_tool_calls','native_tool_results','sdk_shell','sdk_upload','sdk_download']:
                    number=counts.get(name)
                    if type(number)is int and 0<=number<=1000000:detail+='; '+name+'='+str(number)
            raise RuntimeError(redact('original QM native operation failed ('+kind+')'+detail+'; raw diagnostics omitted'))
        if not isinstance(value,dict):raise RuntimeError('original QM result must be an object')
        return redact(value)
    finally:LOCK.release()


@command('qm_sandbox_version',description='Actual original QM/source and Node executable identity, compiled original SDK version; no model/network.')
def native_version() -> dict:
    return invoke('version',{},60)


@command('qm_sandbox_native_check',description='Import unchanged original QM harness/tool context and real SDK client without model or backend connection.')
def native_check() -> dict:
    return invoke('native_check',{},60)


@command('qm_sandbox_setup_check',description='Read-only SDK and explicit model configuration presence, without values/network/setup.')
def setup_check() -> dict:
    return {'mode':'original-qm-agent-sandbox-sdk-slice','sdk_base_set':bool(SDK_BASE),'sdk_token_set':bool(SDK_TOKEN),
            'model_key_set':bool(MODEL['MODEL_API_KEY']),'model_base_set':bool(MODEL['MODEL_BASE_URL']),'model_set':bool(MODEL['MODEL'])}


@command('qm_sandbox_sdk_smoke',description='Original QM tool context uses actual SDK for private file/execution/list/removal and independently absent owned fixture.')
def sdk_smoke() -> str:
    result=invoke('sdk_smoke',{'root':workspace(''),**sdk_settings()},150)
    if not all(result.get(name)is True for name in ['original_qm_tools','actual_agent_sandbox_sdk','owned_cleanup']):raise RuntimeError('original QM SDK round trip incomplete')
    return 'Original QM tools and actual Agent Sandbox SDK round trip/owned cleanup OK'


@command('qm_sandbox_exec',description='Original QM execute tool context through actual SDK with owned per-tool process/descendant cleanup; no model.')
def backend_exec(command: str,cwd: str='',command_timeout: int=60) -> dict:
    if not isinstance(command,str)or not command.strip()or len(command.encode())>32768 or '\0'in command:raise ValueError('command must contain1..32768UTF8 bytes without NUL')
    if type(command_timeout)is not int or not 1<=command_timeout<=120:raise ValueError('command_timeout must be1..120seconds')
    root=workspace(cwd)
    return invoke('exec',{'command':command,'deadline':command_timeout,'root':root,**sdk_settings()},command_timeout+50)


@command('qm_sandbox_file',description='Original QM file context and actual SDK read/write/list/remove within selected existing project; caller artifacts persist.')
def backend_file(action: str,path: str='',text: str='',cwd: str='') -> dict:
    if action not in ['read','write','list','remove']:raise ValueError('action must be read/write/list/remove')
    if not isinstance(path,str)or len(path.encode())>4096 or '\0'in path:raise ValueError('invalid bounded path')
    if not isinstance(text,str)or len(text.encode())>32768:raise ValueError('text must be at most32KiB UTF8')
    root=workspace(cwd)
    target=(Path(root)/path).resolve()
    if not target.is_relative_to(Path(root)):raise ValueError('path must stay inside selected project')
    if action in ['write','remove']and target==Path(root):raise ValueError('cannot replace/remove caller project root')
    return invoke('file',{'action':action,'path':path,'text':text,'root':root,**sdk_settings()},120)


if __name__=='__main__':
    start(int(os.environ.get('ABX_SERVER_PORT','9000')))
