"""Explicit compatible provider for the genuine pinned Factory Droid binary."""
import hashlib,importlib.util,json,os,re,subprocess,tempfile,threading
from pathlib import Path
from urllib.parse import urlsplit
from agent_sandbox.server import command

ROOT=Path(os.environ.get('WORKSPACE','/home/user/app')).resolve()
CONFIG={k:os.environ.get('DROID_'+k,'').strip()for k in ['MODEL_API_KEY','MODEL_BASE_URL','MODEL']}
SHA256='1f50e238df053573aec1dae7b90b19c8e5afca83ab13a790a00f53ba4e4b9ab1'
LOCK=threading.Lock()
spec=importlib.util.spec_from_file_location('droid_owned_process',Path(__file__).with_name('process.py'))
process=importlib.util.module_from_spec(spec);spec.loader.exec_module(process)


def binary():
    path=Path('/opt/droid/node_modules/@factory/cli-linux-x64/bin/droid')
    if not path.is_file()or not os.access(path,os.X_OK)or not 0<path.stat().st_size<=350*1024*1024:
        raise RuntimeError('pinned Linuxx64 Droid distribution unavailable')
    with path.open('rb')as stream:
        if hashlib.file_digest(stream,'sha256').hexdigest()!=SHA256:raise RuntimeError('actual native Droid differs from pinned0.241.1')
    return str(path)


def validate_config():
    if not all(CONFIG.values()):raise ValueError('DROID_MODEL_API_KEY, DROID_MODEL_BASE_URL and DROID_MODEL required before startup')
    base,key,model=CONFIG['MODEL_BASE_URL'],CONFIG['MODEL_API_KEY'],CONFIG['MODEL']
    if len(base)>2048 or any(x.isspace()or ord(x)<32 for x in base):raise ValueError('invalid bounded model base URL')
    try:
        value=urlsplit(base);value.port
    except ValueError:raise ValueError('invalid model base URL')from None
    if not value.hostname or value.username is not None or value.password is not None or value.query or value.fragment or(value.scheme!='https'and not(value.scheme=='http'and value.hostname in ['127.0.0.1','localhost','::1'])):
        raise ValueError('explicit HTTPS compatible base or literal local HTTP required, without userinfo/query/fragment')
    if len(key)>8192 or any(x in key for x in '\r\n\0'):raise ValueError('invalid bounded model key')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}',model):raise ValueError('invalid bounded model identifier')


def environment(home,*,model):
    env={k:os.environ[k]for k in ['SSL_CERT_FILE','SSL_CERT_DIR','NODE_EXTRA_CA_CERTS']if k in os.environ}
    env.update(PATH='/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin',HOME=str(home),TMPDIR=str(home),
        XDG_CACHE_HOME=str(home/'cache'),XDG_CONFIG_HOME=str(home/'config'),XDG_DATA_HOME=str(home/'data'),
        FACTORY_DROID_AUTO_UPDATE_ENABLED='false',DO_NOT_TRACK='1',NO_COLOR='1',TERM='dumb',LANG='C.UTF-8')
    env.update(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null')
    if model:env['ABX_DROID_MODEL_KEY']=CONFIG['MODEL_API_KEY']
    return env


def profile(home):
    settings={'customModels':[{'model':CONFIG['MODEL'],'displayName':'AbxApproved',
        'baseUrl':CONFIG['MODEL_BASE_URL'],'apiKey':'${ABX_DROID_MODEL_KEY}',
        'provider':'generic-chat-completion-api','maxOutputTokens':4096,'maxContextLimit':65536,'noImageSupport':True}]}
    root=home/'.factory';root.mkdir(mode=0o700)
    with(root/'settings.json').open('x')as stream:
        os.chmod(stream.name,0o600);json.dump(settings,stream)


def redact(text):
    for value in [CONFIG['MODEL_API_KEY'],CONFIG['MODEL_BASE_URL']]:
        if value:
            for variant in {value,json.dumps(value)[1:-1],json.dumps(value,ensure_ascii=False)[1:-1]}:
                text=text.replace(variant,'[REDACTED]')
    return text


@command('droid_byok_setup_check',description='Inspect explicit compatible model settings without secret values or model calls.')
def droid_byok_setup_check() -> dict:
    return {'mode':'openai-compatible-byok','factory_account_required':False,
        'base_url_set':bool(CONFIG['MODEL_BASE_URL']),'api_key_set':bool(CONFIG['MODEL_API_KEY']),'model_set':bool(CONFIG['MODEL'])}


@command('droid_byok',description='Run genuine pinned Droid with an explicit compatible model, private native state and bounded coding.')
def droid_byok(prompt: str,cwd: str='',command_timeout: int=300) -> dict:
    if not isinstance(prompt,str)or not prompt.strip()or'\0'in prompt or len(prompt.encode())>32768:
        raise ValueError('prompt must contain1..32768UTF-8 bytes without NUL')
    if not isinstance(cwd,str)or len(cwd.encode())>4096 or'\0'in cwd:raise ValueError('invalid bounded cwd')
    if type(command_timeout)is not int or not 1<=command_timeout<=600:raise ValueError('command_timeout must be1..600seconds')
    directory=(ROOT/cwd).resolve()
    if not directory.is_relative_to(ROOT)or not directory.is_dir():raise ValueError('cwd must exist inside WORKSPACE')
    validate_config()
    if not LOCK.acquire(blocking=False):raise RuntimeError('another Droid BYOK operation is active')
    try:
        native=binary()
        with tempfile.TemporaryDirectory(prefix='abx-droid-home-')as value:
            home=Path(value);home.chmod(0o700);profile(home)
            subprocess.run(['git','init','--quiet',str(home)],env=environment(home,model=False),
                stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,check=True)
            argv=[native,'exec','--model','custom:'+CONFIG['MODEL'],'--output-format','json',
                '--auto','low','--disable-builtin-skills','--settings',str(home/'.factory/settings.json'),
                '--cwd',str(home),'--only-tools','Read,Edit,Create,Grep,Glob,LS']
            request='The project to edit is the existing directory '+json.dumps(str(directory))+'. Use absolute paths in native file tools for that project. Preserve unrelated files and original tests.\n\n'+prompt
            descriptor=os.memfd_create('droid-task',os.MFD_CLOEXEC)
            with os.fdopen(descriptor,'w+b')as stream:
                stream.write(request.encode());stream.seek(0)
                code,out,err=process.run(argv,cwd=home,timeout=command_timeout,env=environment(home,model=True),input_file=stream)
        out,err=redact(out),redact(err)
        return {'exit_code':code,'stdout':out,'stderr':err,'native_version':'0.241.1'}
    finally:LOCK.release()
