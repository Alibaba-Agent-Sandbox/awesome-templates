"""Official pinned native DeepAgents with private compatible-provider configuration."""
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from urllib.parse import urlsplit
from agent_sandbox.server import command,start

spec=importlib.util.spec_from_file_location('deepagents_owned_process',Path(__file__).with_name('process.py'))
process=importlib.util.module_from_spec(spec);spec.loader.exec_module(process)
VERSION='0.7.25'

def _binary():
    value=os.environ.get('DEEPAGENTS_PYTHON','/opt/deepagents/bin/python')
    path=Path(value).absolute()
    if not path.is_file() or not os.access(path,os.X_OK):raise RuntimeError('pinned DeepAgents Python runtime unavailable')
    return str(path)


def _environment(root):
    env={key:os.environ[key] for key in ['PATH','SSL_CERT_FILE','SSL_CERT_DIR'] if key in os.environ}
    env.update(HOME=str(root),LANG='C.UTF-8',LC_ALL='C.UTF-8',XDG_CONFIG_HOME=str(root/'config'),XDG_DATA_HOME=str(root/'data'),XDG_CACHE_HOME=str(root/'cache'),LANGSMITH_TRACING='false',LANGCHAIN_TRACING_V2='false',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_CONFIG_COUNT='2',GIT_CONFIG_KEY_0='core.fsmonitor',GIT_CONFIG_VALUE_0='false',GIT_CONFIG_KEY_1='core.hooksPath',GIT_CONFIG_VALUE_1=os.devnull,NO_COLOR='1')
    return env


def _workspace(cwd):
    root=Path(os.environ.get('WORKSPACE','/home/user/app')).resolve(strict=True)
    if not isinstance(cwd,str) or '\0' in cwd or len(cwd.encode())>4096:raise ValueError('cwd must be a bounded workspace directory')
    target=(Path(cwd) if Path(cwd).is_absolute() else root/cwd).resolve(strict=True)
    if not target.is_dir() or not target.is_relative_to(root):raise ValueError('cwd must stay inside WORKSPACE')
    return target


@command('deepagents_version',description='Inspect actual official DeepAgents0.7.25 without loading caller configuration or calling a model.')
def deepagents_version() -> str:
    with tempfile.TemporaryDirectory(prefix='abx-deepagents-version-') as directory:
        root=Path(directory)
        code,out,_=process.run([_binary(),str(Path(__file__).with_name('worker.py')),'--version'],cwd=root,env=_environment(root),timeout=20)
    if code or out.strip()!=VERSION:raise RuntimeError('actual DeepAgents executable does not match0.7.25')
    return VERSION


@command('deepagents_setup_check',description='Read-only binary/model setting flags; no login or credential values.')
def deepagents_setup_check() -> dict:
    installed=Path(os.environ.get('DEEPAGENTS_PYTHON','/opt/deepagents/bin/python')).is_file()
    return {'installed':installed,'version':deepagents_version() if installed else '',**{name.lower()+'_set':bool(os.environ.get('DEEPAGENTS_'+name,'').strip()) for name in ['API_KEY','BASE_URL','MODEL']}}


@command('deepagents',description='Actual DeepAgents stdin turn with private configuration; explicit tools and bounded owned processes.')
def deepagents(task: str,cwd: str='',allow_tools: bool=False,command_timeout: int=600) -> dict:
    if not isinstance(task,str) or not task.strip() or '\0' in task or len(task.encode())>256*1024:raise ValueError('task must be nonempty UTF-8/no NUL/at most256KiB')
    if type(allow_tools) is not bool or type(command_timeout) is not int or not 1<=command_timeout<=1800:raise ValueError('allow_tools must be boolean and command_timeout1..1800')
    values={key:os.environ.get('DEEPAGENTS_'+key,'').strip() for key in ['API_KEY','BASE_URL','MODEL']}
    if not all(values.values()):raise RuntimeError('DEEPAGENTS_API_KEY, DEEPAGENTS_BASE_URL and DEEPAGENTS_MODEL are required on this server')
    url=urlsplit(values['BASE_URL'])
    if url.scheme not in ('http','https') or not url.hostname or url.username or url.password or url.query or url.fragment:raise ValueError('DEEPAGENTS_BASE_URL requires HTTP(S) without userinfo/query/fragment')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}',values['MODEL']):raise ValueError('model must be a bounded upstream identifier')
    target=_workspace(cwd);deepagents_version()
    with tempfile.TemporaryDirectory(prefix='abx-deepagents-config-') as directory:
        root=Path(directory);root.chmod(0o700);(root/'config').mkdir(mode=0o700);(root/'data').mkdir(mode=0o700)
        config={'task':task,'cwd':str(target),'allow_tools':allow_tools,'command_timeout':command_timeout,'api_key':values['API_KEY'],'base_url':values['BASE_URL'],'model':values['MODEL']}
        with tempfile.TemporaryFile(dir=root) as source:
            source.write(json.dumps(config,ensure_ascii=False).encode());source.seek(0)
            code,out,err=process.run([_binary(),str(Path(__file__).with_name('worker.py'))],cwd=target,env=_environment(root),timeout=command_timeout,input_file=source)
    for value in [values['API_KEY'],values['BASE_URL']]:out=out.replace(value,'[REDACTED]');err=err.replace(value,'[REDACTED]')
    return {'stdout':out,'stderr':err,'exit_code':code}


if __name__=='__main__':start(int(os.environ.get('ABX_SERVER_PORT','9000')))
