"""Original native Muse Code, explicit Responses endpoint and owned per-call state."""
import importlib.util,json,os,tempfile,threading
from pathlib import Path
from agent_sandbox.server import command,start

ROOT=Path(os.environ.get('WORKSPACE','/home/user/app')).resolve()
MODEL={k:os.environ.get('MUSE_'+k,'').strip()for k in ['MODEL_API_KEY','MODEL_BASE_URL','MODEL']}
LOCK=threading.Lock()

def load(name):
    spec=importlib.util.spec_from_file_location('owned_muse_'+name,Path(__file__).with_name(name+'.py'))
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

INSTALL=load('install_runtime');PROCESS=load('process');FILTER=load('filter_native');RELAY=load('relay')
IDENTITY=None


def binary():
    global IDENTITY
    path=Path('/opt/muse/bin/muse')
    try:st=path.stat(follow_symlinks=False)
    except OSError:raise RuntimeError('original pinned Muse executable unavailable')from None
    identity=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns,st.st_mode)
    if identity!=IDENTITY:INSTALL.verify_binary(path);IDENTITY=identity
    if not os.access(path,os.X_OK):raise RuntimeError('original Muse is not executable')
    return str(path)


def workspace(cwd):
    if not isinstance(cwd,str)or len(cwd.encode())>4096 or '\0'in cwd:raise ValueError('invalid bounded cwd')
    path=(ROOT/cwd).resolve()
    if not path.is_relative_to(ROOT)or not path.is_dir():raise ValueError('cwd must be an existing directory inside WORKSPACE')
    return path


def environment(private):
    return {'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':str(private),'TMPDIR':str(private),
            'XDG_CONFIG_HOME':str(private/'config'),'XDG_CACHE_HOME':str(private/'cache'),'XDG_DATA_HOME':str(private/'data'),
            'LANG':'C.UTF-8','NO_COLOR':'1','TERM':'dumb','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null'}


def redact(value):
    secrets=[MODEL['MODEL_API_KEY'],MODEL['MODEL_BASE_URL'],os.environ.get('ABX_SERVER_TOKEN','')]
    if isinstance(value,str):
        for secret in secrets:
            if secret:
                for text in {secret,json.dumps(secret)[1:-1],json.dumps(secret,ensure_ascii=False)[1:-1]}:value=value.replace(text,'[REDACTED]')
    elif isinstance(value,dict):value={k:redact(v)for k,v in value.items()}
    elif isinstance(value,list):value=[redact(v)for v in value]
    return value


def diagnostic(arguments):
    with tempfile.TemporaryDirectory(prefix='abx-muse-check-')as name:
        private=Path(name);private.chmod(0o700)
        code,out,err=PROCESS.run([binary(),*arguments],cwd=private,env=environment(private),timeout=40)
    if code:raise RuntimeError('original Muse diagnostic failed; raw output omitted')
    return out.strip()


@command('muse_version',description='Actual original pinned Muse ELF hash/size and native version; no model/network.')
def native_version() -> str:
    text=diagnostic(['--version'])
    if text!='Muse Code 1.4.11 (1.4.11-R6667.1)':raise RuntimeError('original Muse version differs')
    return text


@command('muse_native_check',description='Actual original headless CLI help and immutable native identity; no model/account call.')
def native_check() -> dict:
    text=diagnostic(['exec','--help'])
    return {'original_native':True,'headless_json':'--json'in text,'anonymous_api_key_stdin':'--api-key-stdin'in text,'no_session_log':'--no-session-log'in text}


@command('muse_setup_check',description='Read-only original native installation and explicit model setting presence; no values/network/authentication.')
def setup_check() -> dict:
    path=Path('/opt/muse/bin/muse')
    return {'mode':'original-native-muse-explicit-responses','native_present':path.is_file()and not path.is_symlink(),
            'model_key_set':bool(MODEL['MODEL_API_KEY']),'model_base_set':bool(MODEL['MODEL_BASE_URL']),'model_set':bool(MODEL['MODEL']),
            'model_account_verified':False,'provider_default_fallback':False,'catalog_relay':True}


@command('muse',description='Bounded original Muse exec/miniswe tool loop using an explicit approved Responses endpoint and local catalogue/credential relay.')
def muse(prompt: str,cwd: str='',command_timeout: int=300) -> dict:
    if not isinstance(prompt,str)or not prompt.strip()or len(prompt.encode())>32768 or '\0'in prompt:raise ValueError('prompt must contain1..32768UTF8 bytes without NUL')
    if type(command_timeout)is not int or not 1<=command_timeout<=600:raise ValueError('command_timeout must be1..600seconds')
    project=workspace(cwd)
    base,key,model=RELAY.settings(MODEL['MODEL_BASE_URL'],MODEL['MODEL_API_KEY'],MODEL['MODEL'])
    if not LOCK.acquire(blocking=False):raise RuntimeError('another native Muse operation is active')
    relay=None
    try:
        executable=binary()
        with tempfile.TemporaryDirectory(prefix='abx-muse-home-')as name:
            private=Path(name);private.chmod(0o700);relay=RELAY.Relay(base,key,model,command_timeout)
            config=private/'config/muse';config.mkdir(parents=True,mode=0o700)
            settings={'schema_version':1,'endpoint_transport':{'base_url':relay.url,'auth':'bearer'},'agents':{'execution_capacity':1}}
            (config/'settings.json').write_text(json.dumps(settings));(config/'settings.json').chmod(0o600)
            argv=[executable,'exec','--json','--api-key-stdin','--provider','meta','--model',model,'--preset','miniswe',
                  '--reasoning-effort','minimal','--max-model-steps','16','--no-session-log','--disable-reminders',
                  '--no-foreign-personal-context','--disable-web-tools','--yolo','--workspace',str(project),prompt]
            descriptor=os.memfd_create('muse-owned-relay-token',os.MFD_CLOEXEC)
            with os.fdopen(descriptor,'w+b')as source:
                source.write((relay.token+'\n').encode());source.seek(0)
                code,out,err=PROCESS.run(argv,cwd=private,env=environment(private),timeout=command_timeout,input_file=source)
            try:result=FILTER.completed(out,code,model)
            except (ValueError,TypeError):raise RuntimeError('original Muse event protocol invalid; raw diagnostics omitted')from None
            relay.wait_for_idle()
            stats=relay.snapshot()
            if code or not result['native_completed']or stats['failed_responses']or stats['completed_responses']<result['model_calls']:
                raise RuntimeError('original Muse native completion incomplete; native_exit_code='+str(code)+'; model_calls='+str(result['model_calls'])+'; native_tool_results='+str(result['native_tool_results'])+'; responses_issued='+str(stats['responses_requests'])+'; responses_completed='+str(stats['completed_responses'])+'; responses_failed='+str(stats['failed_responses'])+'; raw diagnostics omitted')
            result.update(exit_code=0,native_version=INSTALL.VERSION,binary_sha256=INSTALL.EXPECTED['sha256'],
                          model=model,protocol='original-responses',catalog_credential_relay=True,relay_calls=stats)
            result['stdout']=result['stdout'].replace(relay.token,'[REDACTED]').replace(relay.url,'[OWNED_RELAY]')
            return redact(result)
    finally:
        try:
            if relay is not None:relay.close()
        finally:LOCK.release()


if __name__=='__main__':
    start(int(os.environ.get('ABX_SERVER_PORT','9000')))
