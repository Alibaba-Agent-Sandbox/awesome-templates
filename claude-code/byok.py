"""Original Claude CLI with explicit text/tool adapter and per-call owned state."""
import hashlib,importlib.util,json,os,tempfile,threading
from pathlib import Path
ROOT=Path(os.environ.get('WORKSPACE','/home/user/app')).resolve()
MODEL={k:os.environ.get('CLAUDE_'+k,'').strip()for k in ['MODEL_API_KEY','MODEL_BASE_URL','MODEL']}
LOCK=threading.Lock();IDENTITY=None
EXPECTED=json.loads(Path(__file__).with_name('upstream.json').read_text())
def load(name):
    spec=importlib.util.spec_from_file_location('owned_claude_'+name,Path(__file__).with_name(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
PROCESS=load('process');RELAY=load('relay')
def binary():
    global IDENTITY
    path=Path('/opt/claude-code/node_modules/@anthropic-ai/claude-code/cli.js')
    try:st=path.stat(follow_symlinks=False)
    except OSError:raise RuntimeError('original pinned Claude CLI unavailable')from None
    identity=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns,st.st_mode)
    if path.is_symlink()or st.st_uid!=0 or st.st_mode&0o022 or st.st_size!=EXPECTED['cli_bytes']:raise RuntimeError('original Claude script identity differs')
    if identity!=IDENTITY:
        if hashlib.sha256(path.read_bytes()).hexdigest()!=EXPECTED['cli_sha256']:raise RuntimeError('original Claude script SHA256 differs')
        IDENTITY=identity
    return '/usr/bin/env','node',str(path)
def workspace(cwd):
    if not isinstance(cwd,str)or len(cwd.encode())>4096 or '\0'in cwd:raise ValueError('invalid bounded cwd')
    path=(ROOT/cwd).resolve()
    if not path.is_relative_to(ROOT)or not path.is_dir():raise ValueError('cwd must be an existing directory inside WORKSPACE')
    return path
def environment(private):
    return {'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':str(private),'TMPDIR':str(private),'CLAUDE_CONFIG_DIR':str(private/'config'),
            'XDG_CONFIG_HOME':str(private/'xdg'),'XDG_CACHE_HOME':str(private/'cache'),'LANG':'C.UTF-8','NO_COLOR':'1','TERM':'dumb',
            'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','DISABLE_AUTOUPDATER':'1','CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC':'1',
            'DISABLE_TELEMETRY':'1','DISABLE_ERROR_REPORTING':'1','DISABLE_PROMPT_CACHING':'1','MAX_THINKING_TOKENS':'0'}
def diagnostic(args):
    with tempfile.TemporaryDirectory(prefix='abx-claude-check-')as n:
        p=Path(n);p.chmod(0o700);code,out,err=PROCESS.run([*binary(),*args],cwd=p,env=environment(p),timeout=40)
    if code:raise RuntimeError('original Claude diagnostic failed; raw output omitted')
    return out.strip()
def setup():
    return {'mode':'original-claude-explicit-chat-adapter','model_key_set':bool(MODEL['MODEL_API_KEY']),'model_base_set':bool(MODEL['MODEL_BASE_URL']),'model_set':bool(MODEL['MODEL']),'vendor_account_verified':False,'provider_default_fallback':False,'requires_unsafe_optin':True}
def redact(value,relay):
    for secret in [MODEL['MODEL_API_KEY'],MODEL['MODEL_BASE_URL'],os.environ.get('ABX_SERVER_TOKEN',''),relay.token,relay.url]:
        if secret:
            for form in {secret,json.dumps(secret)[1:-1],json.dumps(secret,ensure_ascii=False)[1:-1]}:value=value.replace(form,'[REDACTED]')
    return value

def run(prompt,cwd='',command_timeout=300,allow_unsafe_tools=False):
    if not isinstance(prompt,str)or not prompt.strip()or len(prompt.encode())>32768 or '\0'in prompt:raise ValueError('prompt must contain1..32768UTF8 bytes without NUL')
    if type(command_timeout)is not int or not 1<=command_timeout<=600:raise ValueError('command_timeout must be1..600seconds')
    if type(allow_unsafe_tools)is not bool or not allow_unsafe_tools:raise ValueError('allow_unsafe_tools=True is required for the explicit disposable-sandbox native tool profile')
    project=workspace(cwd);base,key,model=RELAY.settings(MODEL['MODEL_BASE_URL'],MODEL['MODEL_API_KEY'],MODEL['MODEL'])
    if not LOCK.acquire(blocking=False):raise RuntimeError('another original Claude BYOK operation active')
    relay=None
    try:
        argv=list(binary())
        with tempfile.TemporaryDirectory(prefix='abx-claude-home-')as name:
            private=Path(name);private.chmod(0o700);relay=RELAY.Relay(base,key,model,command_timeout);env=environment(private)
            env.update(ANTHROPIC_BASE_URL=relay.url,ANTHROPIC_AUTH_TOKEN=relay.token,ANTHROPIC_MODEL=model,ANTHROPIC_DEFAULT_HAIKU_MODEL=model,ANTHROPIC_DEFAULT_SONNET_MODEL=model,ANTHROPIC_DEFAULT_OPUS_MODEL=model)
            settings={'disableAllHooks':True,'permissions':{'defaultMode':'bypassPermissions'},'enableAllProjectMcpServers':False}
            argv+=['-p',prompt,'--model',model,'--output-format','json','--dangerously-skip-permissions','--tools','Read,Edit,Write,Bash','--allowedTools','Read,Edit,Write,Bash',
                   '--settings',json.dumps(settings),'--setting-sources','','--no-session-persistence','--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--disable-slash-commands','--no-chrome','--max-turns','16']
            code,out,err=PROCESS.run(argv,cwd=project,env=env,timeout=command_timeout);relay.wait_for_idle();stats=relay.snapshot()
            try:value=json.loads(out)
            except ValueError:raise RuntimeError('original Claude output protocol invalid; native_code='+str(code)+'; model_requests='+str(stats['model_requests'])+'; raw diagnostics omitted')from None
            if code or not isinstance(value,dict)or value.get('type')!='result'or value.get('subtype')!='success'or value.get('is_error')is not False or not isinstance(value.get('result'),str)or not value['result'].strip()or not stats['completed_required_responses']or stats['failed_responses']:
                subtype=value.get('subtype')if isinstance(value,dict)else'not-object'
                safe=subtype if subtype in ['success','error_max_turns','error_during_execution','error_max_budget_usd']else'other'
                raise RuntimeError('original Claude completion incomplete; native_code='+str(code)+'; native_subtype='+safe+'; model_requests='+str(stats['model_requests'])+'; native_tool_calls='+str(stats['native_tool_calls'])+'; native_tool_results='+str(stats['native_tool_results'])+'; completed_responses='+str(stats['completed_responses'])+'; failed_responses='+str(stats['failed_responses'])+'; failure_counts='+json.dumps(stats['failure_counts'],sort_keys=True)+'; upstream_status='+str(stats['last_upstream_status'])+'; raw diagnostics omitted')
            return {'stdout':redact(value['result'],relay),'exit_code':0,'native_completed':True,'native_version':'2.0.76','cli_sha256':EXPECTED['cli_sha256'],
                    'permission_profile':'explicit-owned-sandbox-bypass','protocol':'authored-messages-chat-text-tools','model':model,'model_calls':stats['completed_responses'],'native_tool_results':stats['native_tool_results'],'relay_calls':stats}
    finally:
        try:
            if relay is not None:relay.close()
        finally:LOCK.release()
