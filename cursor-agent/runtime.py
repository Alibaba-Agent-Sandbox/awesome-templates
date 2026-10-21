"""Original Cursor CLI in caller-owned disposable sandboxes, with bounded state."""
import hashlib,importlib.util,json,os,re,tempfile,threading
from pathlib import Path

VERSION='2026.10.19-6bbf2c4'
ROOT=Path(os.environ.get('WORKSPACE','/home/user/app')).resolve()
PREFIX=Path('/opt/cursor-agent')
KEY=os.environ.get('CURSOR_API_KEY','').strip()
SERVER_TOKEN=os.environ.get('ABX_SERVER_TOKEN','')
UPSTREAM=json.loads(Path(__file__).with_name('upstream.json').read_text())
LOCK=threading.Lock();IDENTITY=None
spec=importlib.util.spec_from_file_location('owned_cursor_process',Path(__file__).with_name('process.py'))
PROCESS=importlib.util.module_from_spec(spec);spec.loader.exec_module(PROCESS)

def executable():
    global IDENTITY
    try:parent=PREFIX.stat(follow_symlinks=False)
    except OSError:raise RuntimeError('original pinned Cursor package unavailable')from None
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
    return str(PREFIX/'cursor-agent')

def environment(private,key=''):
    env={'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':str(private),'TMPDIR':str(private),'LANG':'C.UTF-8','NO_COLOR':'1','TERM':'dumb','CI':'1',
         'XDG_CONFIG_HOME':str(private/'config'),'XDG_CACHE_HOME':str(private/'cache'),'XDG_DATA_HOME':str(private/'data'),
         'CURSOR_CONFIG_DIR':str(private/'config/cursor'),'CURSOR_DATA_DIR':str(private/'data/cursor'),'NODE_COMPILE_CACHE':str(private/'cache/node'),
         'AGENT_CLI_CREDENTIAL_STORE':'memory','CURSOR_AGENT_PERSIST_SESSION':'0','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null'}
    if key:env['CURSOR_API_KEY']=key
    return env

def diagnostic(arguments):
    with tempfile.TemporaryDirectory(prefix='abx-cursor-check-')as name:
        private=Path(name);private.chmod(0o700)
        code,out,err=PROCESS.run([executable(),'--disable-auto-update','--disable-project-configs',*arguments],cwd=private,env=environment(private),timeout=40)
    if code:raise RuntimeError('original Cursor diagnostic failed; raw output omitted')
    return out.strip()

def workspace(cwd):
    if not isinstance(cwd,str)or len(cwd.encode())>4096 or '\0'in cwd:raise ValueError('invalid bounded cwd')
    path=(ROOT/cwd).resolve()
    if not path.is_relative_to(ROOT)or not path.is_dir():raise ValueError('cwd must be an existing directory inside WORKSPACE')
    return path

def setup():
    return {'mode':'original-cursor-native','installed':PREFIX.is_dir(),'pinned_version':VERSION,'api_key_set':bool(KEY),
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
    if not KEY:raise RuntimeError('CURSOR_API_KEY is required; interactive login and compatible-model fallback are disabled')
    if len(KEY)>8192 or any(ord(c)<32 for c in KEY):raise ValueError('invalid bounded native API key')
    if not LOCK.acquire(blocking=False):raise RuntimeError('another original Cursor operation is active')
    try:
        with tempfile.TemporaryDirectory(prefix='abx-cursor-home-')as name:
            private=Path(name);private.chmod(0o700)
            args=[executable(),'--print','--output-format','json','--disable-auto-update','--disable-project-configs','--sandbox','disabled','--trust','--force','--workspace',str(project)]
            if model:args+=['--model',model]
            args+=[prompt]
            code,out,err=PROCESS.run(args,cwd=project,env=environment(private,KEY),timeout=command_timeout)
            if code:raise RuntimeError('original Cursor failed; native_exit_code='+str(code)+'; category='+failure_category(out+'\n'+err))
            try:value=json.loads(out)
            except ValueError:raise RuntimeError('original Cursor completed output is not JSON; raw output omitted')from None
            if not isinstance(value,dict)or value.get('type')!='result'or value.get('subtype')!='success'or value.get('is_error')is not False or not isinstance(value.get('result'),str)or not value['result'].strip():raise RuntimeError('original Cursor completion is incomplete; raw output omitted')
            text=value['result']
            for secret in [KEY,SERVER_TOKEN,str(private)]:
                if secret:
                    for form in {secret,json.dumps(secret)[1:-1],json.dumps(secret,ensure_ascii=False)[1:-1]}:text=text.replace(form,'[REDACTED]')
            return {'stdout':text,'stderr':'','exit_code':0,'native_completed':True,'native_version':VERSION,
                    'archive_sha256':UPSTREAM['archive']['sha256'],'permission_profile':'explicit-owned-sandbox-bypass','requested_model':model}
    finally:LOCK.release()
