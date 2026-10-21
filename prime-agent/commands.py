"""Original stable Prime Agent, explicit provider and an owned native CPython REPL."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
from urllib.parse import urlsplit
from agent_sandbox.server import command,start

ROOT=Path(os.environ.get('WORKSPACE','/home/user/workspace')).resolve()
CONFIG={name:os.environ.get('PRIME_'+name,'').strip() for name in ['MODEL_API_KEY','MODEL_BASE_URL','MODEL']}
LOCK=threading.Lock()
NATIVE_SHA256='546e71921bb0fa278c9d50dd8c61a27b835413552cb08a9359d0e320848e39d6'
spec=importlib.util.spec_from_file_location('prime_owned_process',Path(__file__).with_name('process.py'))
PROCESS=importlib.util.module_from_spec(spec)
spec.loader.exec_module(PROCESS)


def native_binary():
    path=Path('/opt/prime-agent/prime-agent')
    if not path.is_file() or not os.access(path,os.X_OK) or path.stat().st_size!=61057216:
        raise RuntimeError('original pinned native Prime Agent unavailable')
    with path.open('rb') as source:
        if hashlib.file_digest(source,'sha256').hexdigest()!=NATIVE_SHA256:
            raise RuntimeError('original native Prime Agent binary integrity differs')
    return str(path)


def validate_config():
    if not all(CONFIG.values()):
        raise ValueError('PRIME_MODEL_API_KEY, PRIME_MODEL_BASE_URL and PRIME_MODEL required before startup')
    base,key,model=CONFIG['MODEL_BASE_URL'],CONFIG['MODEL_API_KEY'],CONFIG['MODEL']
    if len(base)>2048 or any(value.isspace() or ord(value)<32 for value in base):
        raise ValueError('invalid bounded model base')
    try:
        value=urlsplit(base)
        value.port
    except ValueError:
        raise ValueError('invalid model base port') from None
    if (not value.hostname or value.username is not None or value.password is not None or value.query or value.fragment
            or (value.scheme!='https' and not (value.scheme=='http' and value.hostname in ['127.0.0.1','localhost','::1']))):
        raise ValueError('explicit HTTPS base or literal local HTTP without userinfo/query/fragment required')
    if len(key)>8192 or any(value in key for value in '\r\n\0'):
        raise ValueError('invalid bounded model key')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}',model):
        raise ValueError('invalid bounded model identifier')


def environment(root,model):
    env={name:os.environ[name] for name in ['SSL_CERT_FILE','SSL_CERT_DIR'] if name in os.environ}
    env.update(PATH='/opt/prime-kernel/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin',
        HOME=str(root),TMPDIR=str(root),XDG_CACHE_HOME=str(root/'cache'),XDG_CONFIG_HOME=str(root/'config'),
        XDG_DATA_HOME=str(root/'data'),PRIME_AGENT_CODING_AGENT_DIR=str(root/'agent'),
        PRIME_AGENT_KERNEL_PYTHON='/opt/prime-kernel/bin/abx-kernel-python',
        PI_OFFLINE='1',NO_COLOR='1',TERM='dumb',LANG='C.UTF-8',
        OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null')
    if model:
        validate_config()
        env['ABX_PRIME_MODEL_KEY']=CONFIG['MODEL_API_KEY']
    return env


def profile(root,model):
    agent=root/'agent'
    agent.mkdir(mode=0o700)
    settings={'onboardingShown':True,'onboardingCompleted':True,'rlmMaxDepth':0,
        'telemetry':{'enabled':False,'noticeShown':True,'localMirror':False},
        'agentTraces':{'enabled':False},'autoRefine':{'enabled':False},
        'compaction':{'enabled':False,'agentCallable':False},
        'retry':{'enabled':False,'maxRetries':0,'failover':{'enabled':False},
                 'provider':{'timeoutMs':60000,'waitForUsage':{'enabled':False}}},
        'factory':{'enabled':False},'mcpServers':{},'packages':[],
        'enableBuiltinSkills':False,'enableSkillCommands':False,'quietStartup':True,
        'idleEvictionMinutes':'off','sessionArchiveMaxAgeDays':'off','sessionArchiveMaxSessions':'off'}
    if model:
        settings.update(defaultProvider='abx-approved',defaultModel=CONFIG['MODEL'],defaultThinkingLevel='off')
        providers={'providers':{'abx-approved':{'api':'openai-completions',
            'baseUrl':CONFIG['MODEL_BASE_URL'],'apiKey':'ABX_PRIME_MODEL_KEY',
            'models':[{'id':CONFIG['MODEL'],'name':'Approved model','reasoning':False,
                       'input':['text'],'contextWindow':65536,'maxTokens':8192}]}}}
        with (agent/'models.json').open('x') as output:
            os.chmod(output.name,0o600)
            json.dump(providers,output)
    with (agent/'settings.json').open('x') as output:
        os.chmod(output.name,0o600)
        json.dump(settings,output)


def terminal_success(stdout):
    try:
        rows=[json.loads(line) for line in stdout.splitlines() if line.strip()]
    except (ValueError,TypeError):
        return False
    if any(isinstance(row,dict)and row.get('type')=='error'for row in rows):
        return False
    endings=[row for row in rows if isinstance(row,dict) and row.get('type')=='agent_end']
    if not endings or not any(isinstance(row,dict) and row.get('type')=='turn_end' for row in rows):
        return False
    messages=endings[-1].get('messages')
    if not isinstance(messages,list):
        return False
    assistants=[message for message in messages if isinstance(message,dict) and message.get('role')=='assistant']
    return bool(assistants) and assistants[-1].get('stopReason')=='stop'


def run_native(args,*,timeout,model,prompt=None,project=None):
    if not LOCK.acquire(blocking=False):
        raise RuntimeError('another native Prime Agent operation is active')
    try:
        binary=native_binary()
        with tempfile.TemporaryDirectory(prefix='abx-prime-home-') as value:
            private=Path(value)
            private.chmod(0o700)
            env=environment(private,model)
            profile(private,model)
            if prompt is None:
                code,out,err=PROCESS.run([binary,*args],cwd=private,env=env,timeout=timeout)
            else:
                work=private/'native-work'
                work.mkdir(mode=0o700)
                git_env=dict(env)
                git_env.pop('ABX_PRIME_MODEL_KEY',None)
                subprocess.run(['/usr/bin/git','init','--quiet',str(work)],env=git_env,
                    stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10,check=True)
                text='Work only on the existing project at absolute path '+json.dumps(str(project))+'. Do not delegate, create subagents, change provider settings or use network services. Use the original ipython tool for file operations and tests.\n\n'+prompt
                descriptor=os.memfd_create('prime-prompt',os.MFD_CLOEXEC)
                with os.fdopen(descriptor,'w+b') as source:
                    source.write(text.encode())
                    source.seek(0)
                    argv=[sys.executable,str(Path(__file__).with_name('filter_native.py')),
                        '--offline','--mode','json','--provider','abx-approved','--model',CONFIG['MODEL'],
                        '--thinking','off','--no-session','--no-skills','--no-prompt-templates','--no-themes',
                        '--no-context-files','--cwd',str(work),'--print']
                    code,out,err=PROCESS.run(argv,cwd=work,env=env,timeout=timeout,input_file=source)
        for secret in [CONFIG['MODEL_API_KEY'],CONFIG['MODEL_BASE_URL']]:
            if secret:
                for escaped in {secret,json.dumps(secret,ensure_ascii=True)[1:-1],json.dumps(secret,ensure_ascii=False)[1:-1]}:
                    out=out.replace(escaped,'[REDACTED]')
                    err=err.replace(escaped,'[REDACTED]')
        return {'stdout':out,'stderr':err,'exit_code':code,'native_version':'0.10.0',
                'native_completed':prompt is not None and code==0 and terminal_success(out)}
    finally:
        LOCK.release()


@command('prime_agent_version',description='Verify the actual original stable native binary SHA256/version without model credentials.')
def prime_agent_version() -> dict:
    value=run_native(['--version'],timeout=30,model=False)
    if value['exit_code']!=0 or value['stdout'].strip()!='0.10.0':
        raise RuntimeError('actual native Prime Agent version differs')
    return {'native_version':'0.10.0'}


@command('prime_agent_kernel_check',description='Verify original CPython REPL protocol/hooks and all locked default imports without model/bootstrap/network.')
def prime_agent_kernel_check() -> dict:
    if not LOCK.acquire(blocking=False):
        raise RuntimeError('another native Prime Agent operation is active')
    try:
        native_binary()
        script="import json,rlm,rlm.repl; assert rlm.repl.PROTOCOL_VERSION==3; assert all(callable(getattr(rlm,n,None)) for n in ['spawn','create_session','host_request','progress_note','rename']); import requests,httpx,yaml,tomli,dotenv,pandas,numpy,scipy,bs4,lxml,pydantic,tyro; print(json.dumps({'protocol_version':3,'required_imports_checked':12}))"
        with tempfile.TemporaryDirectory(prefix='abx-prime-kernel-check-') as value:
            root=Path(value)
            root.chmod(0o700)
            env=environment(root,False)
            profile(root,False)
            code,out,err=PROCESS.run(['/opt/prime-kernel/bin/abx-kernel-python','-c',script],cwd=root,env=env,timeout=60)
        if code:
            raise RuntimeError('original fixed CPython runtime/import check failed; raw diagnostics omitted')
        result=json.loads(out)
        if result!={'protocol_version':3,'required_imports_checked':12}:
            raise RuntimeError('original native kernel protocol/import result differs')
        return result
    finally:
        LOCK.release()


@command('prime_agent_setup_check',description='Read-only explicit compatible model configuration presence; no native kernel/bootstrap/network.')
def prime_agent_setup_check() -> dict:
    return {'mode':'original-native-prime-cpython-repl','subscription_required':False,
            'base_url_set':bool(CONFIG['MODEL_BASE_URL']),'api_key_set':bool(CONFIG['MODEL_API_KEY']),
            'model_set':bool(CONFIG['MODEL'])}


@command('prime_agent',description='Bounded original native Prime Agent coding with an explicit compatible model and private original CPython REPL runtime.')
def prime_agent(prompt: str,cwd: str='',command_timeout: int=300) -> dict:
    if not isinstance(prompt,str) or not prompt.strip() or '\0' in prompt or len(prompt.encode())>32768:
        raise ValueError('prompt must contain1..32768UTF8 bytes without NUL')
    if not isinstance(cwd,str) or len(cwd.encode())>4096 or '\0' in cwd:
        raise ValueError('invalid bounded cwd')
    if type(command_timeout) is not int or not 1<=command_timeout<=600:
        raise ValueError('command_timeout must be1..600seconds')
    directory=(ROOT/cwd).resolve()
    if not directory.is_relative_to(ROOT) or not directory.is_dir():
        raise ValueError('cwd must exist inside WORKSPACE')
    validate_config()
    return run_native([],timeout=command_timeout,model=True,prompt=prompt,project=directory)


if __name__=='__main__':
    start(int(os.environ.get('ABX_SERVER_PORT','9000')))
