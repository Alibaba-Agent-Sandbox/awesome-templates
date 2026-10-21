"""Original Gemini CLI with explicit text/tool adapter and per-call owned state."""
import hashlib,importlib.util,json,os,tempfile,threading
from pathlib import Path
ROOT=Path(os.environ.get('WORKSPACE','/home/user/app')).resolve()
MODEL={k:os.environ.get('GEMINI_BYOK_'+suffix,'').strip()for k,suffix in [('MODEL_API_KEY','API_KEY'),('MODEL_BASE_URL','BASE_URL'),('MODEL','MODEL')]}
LOCK=threading.Lock();IDENTITY=None
PROFILE=Path('/opt/gemini/profile.json')
PROFILE_SHA256='3cbdf52203844a5265ebfd94262c5df78a7e255166ee17a99f24bc811fd78246'
EXPECTED=json.loads(Path(__file__).with_name('upstream.json').read_text())
def load(name):
    spec=importlib.util.spec_from_file_location('owned_gemini_'+name,Path(__file__).with_name(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
PROCESS=load('process');RELAY=load('relay')
def profile():
    try:st=PROFILE.stat(follow_symlinks=False)
    except OSError:raise RuntimeError('trusted root-owned Gemini profile unavailable')from None
    if PROFILE.is_symlink()or st.st_uid!=0 or st.st_mode&0o022 or st.st_size>4096:raise RuntimeError('trusted root-owned Gemini profile identity differs')
    if hashlib.sha256(PROFILE.read_bytes()).hexdigest()!=PROFILE_SHA256:raise RuntimeError('trusted Gemini profile SHA256 differs')
    return str(PROFILE)

def binary():
    global IDENTITY
    root=Path('/opt/gemini/node_modules/@google/gemini-cli');current=[]
    for entry in EXPECTED['files']:
        path=root/entry['path']
        try:st=path.stat(follow_symlinks=False)
        except OSError:raise RuntimeError('original pinned Gemini package unavailable')from None
        if path.is_symlink()or st.st_uid!=0 or st.st_mode&0o022 or st.st_size!=entry['size']:raise RuntimeError('original Gemini package identity differs')
        current.append((st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns,st.st_mode))
    if current!=IDENTITY:
        for entry in EXPECTED['files']:
            if hashlib.file_digest((root/entry['path']).open('rb'),'sha256').hexdigest()!=entry['sha256']:raise RuntimeError('original Gemini package SHA256 differs')
        IDENTITY=current
    return '/usr/bin/env','node',str(root/'bundle/gemini.js')

def workspace(cwd):
    if not isinstance(cwd,str)or len(cwd.encode())>4096 or '\0'in cwd:raise ValueError('invalid bounded cwd')
    path=(ROOT/cwd).resolve()
    if not path.is_relative_to(ROOT)or not path.is_dir():raise ValueError('cwd must be an existing directory inside WORKSPACE')
    return path
def environment(private):
    return {'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':str(private),'TMPDIR':str(private),'GEMINI_CLI_HOME':str(private),
            'XDG_CONFIG_HOME':str(private/'config'),'XDG_CACHE_HOME':str(private/'cache'),'LANG':'C.UTF-8','NO_COLOR':'1','TERM':'dumb',
            'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GEMINI_TELEMETRY_ENABLED':'false','GEMINI_CLI_NO_RELAUNCH':'1'}

def diagnostic(args):
    with tempfile.TemporaryDirectory(prefix='abx-gemini-check-')as n:
        p=Path(n);p.chmod(0o700);code,out,err=PROCESS.run([*binary(),*args],cwd=p,env=environment(p),timeout=40)
    if code:raise RuntimeError('original Gemini diagnostic failed; raw output omitted')
    return out.strip()
def setup():
    return {'mode':'original-gemini-explicit-chat-adapter','model_key_set':bool(MODEL['MODEL_API_KEY']),'model_base_set':bool(MODEL['MODEL_BASE_URL']),'model_set':bool(MODEL['MODEL']),'vendor_account_verified':False,'provider_default_fallback':False}
def redact(value,relay):
    for secret in [MODEL['MODEL_API_KEY'],MODEL['MODEL_BASE_URL'],os.environ.get('ABX_SERVER_TOKEN',''),relay.token,relay.url]:
        if secret:
            for form in {secret,json.dumps(secret)[1:-1],json.dumps(secret,ensure_ascii=False)[1:-1]}:value=value.replace(form,'[REDACTED]')
    return value

def run(prompt,cwd='',command_timeout=300):
    if not isinstance(prompt,str)or not prompt.strip()or len(prompt.encode())>32768 or '\0'in prompt:raise ValueError('prompt must contain1..32768UTF8 bytes without NUL')
    if type(command_timeout)is not int or not 1<=command_timeout<=600:raise ValueError('command_timeout must be1..600seconds')
    project=workspace(cwd);base,key,model=RELAY.settings(MODEL['MODEL_BASE_URL'],MODEL['MODEL_API_KEY'],MODEL['MODEL'])
    if not LOCK.acquire(blocking=False):raise RuntimeError('another original Gemini BYOK operation active')
    relay=None
    try:
        argv=list(binary())
        with tempfile.TemporaryDirectory(prefix='abx-gemini-home-')as name:
            private=Path(name);private.chmod(0o700);relay=RELAY.Relay(base,key,model,command_timeout);env=environment(private)
            env.update(GOOGLE_GEMINI_BASE_URL=relay.url,GOOGLE_GENAI_API_VERSION='v1beta',GEMINI_API_KEY=relay.token,GEMINI_API_KEY_AUTH_MECHANISM='bearer')
            env['GEMINI_CLI_SYSTEM_SETTINGS_PATH']=profile()
            argv+=['--prompt',prompt+'\nThe existing target project is '+str(project)+'. Use absolute paths for all project reads/edits/artifacts.','--model',model,'--output-format','json','--approval-mode','yolo','--include-directories',str(project)]
            code,out,err=PROCESS.run(argv,cwd=private,env=env,timeout=command_timeout);relay.wait_for_idle();stats=relay.snapshot()
            try:value=json.loads(out)
            except ValueError:raise RuntimeError('original Gemini output protocol invalid; native_code='+str(code)+'; model_requests='+str(stats['model_requests'])+'; raw diagnostics omitted')from None
            if code or not isinstance(value,dict)or value.get('error')or not isinstance(value.get('response'),str)or not value['response'].strip()or not stats['completed_responses']or stats['failed_responses']:
                raise RuntimeError('original Gemini completion incomplete; native_code='+str(code)+'; model_requests='+str(stats['model_requests'])+'; native_tool_calls='+str(stats['native_tool_calls'])+'; native_tool_results='+str(stats['native_tool_results'])+'; completed_responses='+str(stats['completed_responses'])+'; failed_responses='+str(stats['failed_responses'])+'; failure_counts='+json.dumps(stats['failure_counts'],sort_keys=True)+'; upstream_status='+str(stats['last_upstream_status'])+'; raw diagnostics omitted')
            return {'stdout':redact(value['response'],relay),'exit_code':0,'native_completed':True,'native_version':'0.64.0','archive_sha256':EXPECTED['archive_sha256'],
                    'protocol':'authored-generatecontent-chat-text-tools','model':model,'model_calls':stats['completed_responses'],'native_tool_results':stats['native_tool_results'],'relay_calls':stats}

    finally:
        try:
            if relay is not None:relay.close()
        finally:LOCK.release()
