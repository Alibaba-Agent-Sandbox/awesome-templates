"""Original Devin CLI in caller-owned disposable sandboxes, with bounded state."""
import hashlib,importlib.util,json,os,re,stat,tempfile,threading,tomllib
from pathlib import Path

VERSION='3000.11.92'
ROOT=Path(os.environ.get('WORKSPACE','/home/user/app')).resolve()
PREFIX=Path('/opt/devin')
CREDENTIALS_FILE=os.environ.get('DEVIN_CREDENTIALS_FILE','').strip()
SERVER_TOKEN=os.environ.get('ABX_SERVER_TOKEN','')
UPSTREAM=json.loads(Path(__file__).with_name('upstream.json').read_text())
LOCK=threading.Lock();IDENTITY=None
spec=importlib.util.spec_from_file_location('owned_devin_process',Path(__file__).with_name('process.py'))
PROCESS=importlib.util.module_from_spec(spec);spec.loader.exec_module(PROCESS)

def executable():
    global IDENTITY
    try:parent=PREFIX.stat(follow_symlinks=False)
    except OSError:raise RuntimeError('original pinned Devin package unavailable')from None
    if PREFIX.is_symlink()or parent.st_uid!=0 or parent.st_mode&0o022:raise RuntimeError('original package directory identity differs')
    current=[]
    for item in UPSTREAM['files']:
        path=PREFIX/item['path']
        try:stat=path.stat(follow_symlinks=False)
        except OSError:raise RuntimeError('original package file unavailable')from None
        if path.is_symlink()or stat.st_uid!=0 or stat.st_mode&0o022 or stat.st_size!=item['size']:raise RuntimeError('original package file identity differs')
        current.append((stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns,stat.st_mode))
    if current!=IDENTITY:
        for item in UPSTREAM['files']:
            with(PREFIX/item['path']).open('rb')as source:
                if hashlib.file_digest(source,'sha256').hexdigest()!=item['sha256']:raise RuntimeError('original package file SHA256 differs')
        IDENTITY=current
    return str(PREFIX/'bin/devin')

def environment(private):
    return {'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':str(private),'TMPDIR':str(private),'LANG':'C.UTF-8','NO_COLOR':'1','TERM':'dumb','CI':'1',
            'XDG_CONFIG_HOME':str(private/'config'),'XDG_CACHE_HOME':str(private/'cache'),'XDG_DATA_HOME':str(private/'data'),
            'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null'}

def configuration(private):
    path=private/'config.json'
    path.write_text(json.dumps({'auto_update':False,'subagents_enabled':False,'read_config_from':{k:False for k in ['agents_standard','cursor','windsurf','claude','copilot','opencode','zed']}}))
    path.chmod(0o600)
    return str(path)

def diagnostic(arguments):
    with tempfile.TemporaryDirectory(prefix='abx-devin-check-')as name:
        private=Path(name);private.chmod(0o700)
        code,out,err=PROCESS.run([executable(),'--config',configuration(private),*arguments],cwd=private,env=environment(private),timeout=40)
    if code:raise RuntimeError('original Devin diagnostic failed; raw output omitted')
    return out.strip()

def credentials():
    if not CREDENTIALS_FILE:return b'',[]
    path=Path(CREDENTIALS_FILE)
    if not path.is_absolute()or path.resolve().is_relative_to(ROOT):raise ValueError('credentials file must be absolute and outside WORKSPACE')
    try:
        descriptor=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
        with os.fdopen(descriptor,'rb')as stream:
            info=os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode)or info.st_uid not in {0,os.geteuid()}or info.st_mode&0o077 or not 0<info.st_size<=65536:raise ValueError('credentials file identity or private mode differs')
            data=stream.read(65537)
        if len(data)>65536:raise ValueError('credentials file exceeds65536bytes')
        parsed=tomllib.loads(data.decode('utf-8'))
    except (OSError,ValueError,RecursionError):raise ValueError('invalid private original credentials TOML file; values omitted')from None
    secrets=[]
    def visit(value,depth=0):
        if depth>64:raise ValueError('credentials TOML nesting exceeds bound')
        if isinstance(value,str)and len(value)>=4:secrets.append(value)
        elif isinstance(value,dict):
            for item in value.values():visit(item,depth+1)
        elif isinstance(value,list):
            for item in value:visit(item,depth+1)
    visit(parsed)
    return data,secrets

def workspace(cwd):
    if not isinstance(cwd,str)or len(cwd.encode())>4096 or '\0'in cwd:raise ValueError('invalid bounded cwd')
    path=(ROOT/cwd).resolve()
    if not path.is_relative_to(ROOT)or not path.is_dir():raise ValueError('cwd must be an existing directory inside WORKSPACE')
    return path

def setup():
    return {'mode':'original-devin-native','installed':PREFIX.is_dir(),'pinned_version':VERSION,'credentials_file_set':bool(CREDENTIALS_FILE),
            'requires_unsafe_optin':True,'vendor_authentication_verified':False,'compatible_model_fallback':False}

def failure_category(text):
    value=text.lower()
    if any(x in value for x in ['401','unauth','authentication','not logged','log in','login'])or('invalid'in value and'key'in value):return 'authentication_refused'
    if any(x in value for x in ['namespace','operation not permitted','sandbox']):return 'runtime_unavailable'
    if any(x in value for x in ['certificate','fetch failed','failed to connect','network','timed out']):return 'network_error'
    return 'native_error'

def run(prompt,cwd='',command_timeout=300,allow_unsafe_tools=False,model=''):
    if not isinstance(prompt,str)or not prompt.strip()or len(prompt.encode())>32768 or '\0'in prompt:raise ValueError('prompt must contain1..32768UTF8 bytes without NUL')
    if type(command_timeout)is not int or not 1<=command_timeout<=600:raise ValueError('command_timeout must be integer1..600seconds')
    if type(allow_unsafe_tools)is not bool or not allow_unsafe_tools:raise ValueError('allow_unsafe_tools=True is required on an owned disposable sandbox')
    if not isinstance(model,str)or(model and not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}',model)):raise ValueError('invalid bounded model identifier')
    project=workspace(cwd)
    # Refuse local native configuration; the fixed private profile owns updates/imports.
    if any((parent/'.devin').exists()or(parent/'.devin').is_symlink()for parent in [project,*project.parents]):raise ValueError('native project .devin configuration is outside this fixed profile')
    credential_bytes,credential_secrets=credentials()
    if not LOCK.acquire(blocking=False):raise RuntimeError('another original Devin operation is active')
    try:
        with tempfile.TemporaryDirectory(prefix='abx-devin-home-')as name:
            private=Path(name);private.chmod(0o700)
            if credential_bytes:
                target=private/'data/devin/credentials.toml';target.parent.mkdir(parents=True,mode=0o700);target.write_bytes(credential_bytes);target.chmod(0o600)
            args=[executable(),'--config',configuration(private),'--permission-mode','dangerous','--respect-workspace-trust','false']
            if model:args+=['--model',model]
            args+=['--print',prompt]
            code,out,err=PROCESS.run(args,cwd=project,env=environment(private),timeout=command_timeout)
            if code:raise RuntimeError('original Devin failed; native_exit_code='+str(code)+'; category='+failure_category(out+'\n'+err))
            if not out.strip():raise RuntimeError('original Devin completed output is empty; raw output omitted')
            text=out.strip()
            for secret in sorted({*credential_secrets,SERVER_TOKEN,str(private),CREDENTIALS_FILE},key=len,reverse=True):
                if secret:
                    for form in {secret,json.dumps(secret)[1:-1],json.dumps(secret,ensure_ascii=False)[1:-1]}:text=text.replace(form,'[REDACTED]')
            return {'stdout':text,'stderr':'','exit_code':0,'native_completed':True,'native_version':VERSION,
                    'archive_sha256':UPSTREAM['archive']['sha256'],'permission_profile':'explicit-owned-sandbox-bypass','requested_model':model}
    finally:LOCK.release()
