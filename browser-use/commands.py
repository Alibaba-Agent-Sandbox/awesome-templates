"""Pinned native browser-use with per-call private browser/process ownership."""
import importlib.util,json,os,re,secrets,tempfile,threading
from pathlib import Path
from urllib.parse import urlsplit
from agent_sandbox.server import command,start
spec=importlib.util.spec_from_file_location('browser_use_owned_process',Path(__file__).with_name('process.py'));process=importlib.util.module_from_spec(spec);spec.loader.exec_module(process)
VERSION='0.13.11'
_OPERATION_LOCK=threading.Lock()

def _python():
    path=Path(os.environ.get('BROWSER_USE_PYTHON','/opt/browser-use/bin/python')).absolute()
    if not path.is_file() or not os.access(path,os.X_OK):raise RuntimeError('pinned native browser-use Python unavailable')
    return str(path)

def _browser():
    path=Path(os.environ.get('BROWSER_USE_BROWSER_BINARY',str(Path(os.environ.get('PLAYWRIGHT_BROWSERS_PATH','/opt/playwright'))/'chromium-1208/chrome-linux64/chrome'))).absolute()
    if not path.is_file() or not os.access(path,os.X_OK):raise RuntimeError('pinned Chromium1208 executable unavailable')
    with tempfile.TemporaryDirectory(prefix='abx-browser-use-browser-version-') as directory:
        root=Path(directory);code,out,_=process.run([str(path),'--version'],cwd=root,env=_environment(root),timeout=15)
    if code or out.strip()!='Google Chrome for Testing 145.0.7632.6':raise RuntimeError('actual Chromium executable differs from pinned1208/145.0.7632.6')
    return str(path)

def _environment(root):
    env={key:os.environ[key] for key in ['PATH','SSL_CERT_FILE','SSL_CERT_DIR'] if key in os.environ}
    env.update(HOME=str(root),LANG='C.UTF-8',LC_ALL='C.UTF-8',XDG_CONFIG_HOME=str(root/'config'),XDG_DATA_HOME=str(root/'data'),XDG_CACHE_HOME=str(root/'cache'),BROWSER_USE_SETUP_LOGGING='false',BROWSER_USE_LOGGING_LEVEL='critical',ANONYMIZED_TELEMETRY='false',BROWSER_USE_CLOUD_SYNC='false',BROWSER_USE_ACTION_TIMEOUT_S='30',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull)
    return env

def _invoke_worker(value,timeout):
    with tempfile.TemporaryDirectory(prefix='abx-browser-use-') as directory:
        root=Path(directory);root.chmod(0o700)
        with tempfile.TemporaryFile(dir=root) as source:
            source.write(json.dumps(value,ensure_ascii=False).encode());source.seek(0)
            code,out,_=process.run([_python(),str(Path(__file__).with_name('worker.py'))],cwd=root,env=_environment(root),timeout=timeout,input_file=source)
    if code:raise RuntimeError('native browser-use execution failed; private diagnostics omitted')
    try:result=json.loads(out)
    except (ValueError,TypeError):raise RuntimeError('native browser-use returned invalid result') from None
    for key in ['BROWSER_USE_API_KEY','BROWSER_USE_BASE_URL']:
        value=os.environ.get(key,'')
        if value:
            for field in ['result','final_url']:
                if isinstance(result.get(field),str):result[field]=result[field].replace(value,'[REDACTED]')
    return result

def _invoke(value,timeout):
    if not _OPERATION_LOCK.acquire(blocking=False):raise RuntimeError('another browser-use operation is active')
    try:return _invoke_worker(value,timeout)
    finally:_OPERATION_LOCK.release()

@command('browser_use_version',description='Read actual pinned browser-use0.13.11 without a browser/model call.')
def browser_use_version() -> str:
    with tempfile.TemporaryDirectory(prefix='abx-browser-use-version-') as directory:
        root=Path(directory);code,out,_=process.run([_python(),str(Path(__file__).with_name('worker.py')),'--version'],cwd=root,env=_environment(root),timeout=15)
    if code or out.strip()!=VERSION:raise RuntimeError('actual browser-use package differs from0.13.11')
    return VERSION

@command('browser_use_setup_check',description='Read-only installed runtime/browser/model flags; no credential values.')
def browser_use_setup_check() -> dict:
    installed=Path(os.environ.get('BROWSER_USE_PYTHON','/opt/browser-use/bin/python')).is_file()
    try:_browser();browser_installed=True
    except RuntimeError:browser_installed=False
    return {'installed':installed,'version':browser_use_version() if installed else '', 'browser_installed':browser_installed, **{name.lower()+'_set':bool(os.environ.get('BROWSER_USE_'+name,'').strip()) for name in ['API_KEY','BASE_URL','MODEL']}}

@command('browser_use_self_test',description='Actual offline native CDP navigation/title/PNG and owned browser cleanup; no model.')
def browser_use_self_test() -> str:
    browser_use_version();result=_invoke({'mode':'self-test','browser_binary':_browser()},60)
    if result.get('self_test')!='BROWSER_USE_NATIVE_OK' or result.get('png_bytes',0)<1000:raise RuntimeError('native browser-use self test failed')
    return 'BROWSER_USE_NATIVE_OK'

@command('browser_use',description='Real native text-DOM browser agent with private local Chromium and new PNG artifact.')
def browser_use(task: str,url: str='',max_steps: int=8,command_timeout: int=300) -> dict:
    if not isinstance(task,str) or not task.strip() or '\0' in task or len(task.encode())>256*1024:raise ValueError('task must be nonempty/no NUL/max256KiB UTF-8')
    if type(max_steps) is not int or not 1<=max_steps<=20 or type(command_timeout) is not int or not 1<=command_timeout<=900:raise ValueError('max_steps1..20 and command_timeout1..900 must be integers')
    if not isinstance(url,str) or len(url.encode())>8192 or '\0' in url:raise ValueError('url must be HTTP(S) and at most8192 UTF-8 bytes')
    if url:
        target=urlsplit(url)
        if target.scheme not in ['http','https'] or not target.hostname or target.username or target.password:raise ValueError('url must be HTTP(S) without userinfo')
    values={key:os.environ.get('BROWSER_USE_'+key,'').strip() for key in ['API_KEY','BASE_URL','MODEL']}
    if not all(values.values()):raise RuntimeError('BROWSER_USE_API_KEY, BROWSER_USE_BASE_URL and BROWSER_USE_MODEL are required on this server')
    endpoint=urlsplit(values['BASE_URL'])
    if endpoint.scheme not in ['http','https'] or not endpoint.hostname or endpoint.username or endpoint.password or endpoint.query or endpoint.fragment:raise ValueError('model endpoint must be HTTP(S) without userinfo/query/fragment')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}',values['MODEL']):raise ValueError('model identifier is invalid')
    browser_use_version();binary=_browser();root=Path(os.environ.get('WORKSPACE','/home/user/app')).resolve(strict=True)
    if not root.is_dir():raise ValueError('WORKSPACE must exist')
    directory=root/'browser-use-artifacts'
    if directory.is_symlink():raise ValueError('artifact directory must not be a symlink')
    directory.mkdir(exist_ok=True);artifact=directory/(secrets.token_hex(16)+'.png')
    with artifact.open('xb'):pass
    try:
        result=_invoke({'mode':'agent','task':task,'url':url,'max_steps':max_steps,'browser_binary':binary,'api_key':values['API_KEY'],'base_url':values['BASE_URL'],'model':values['MODEL'],'screenshot_path':str(artifact)},command_timeout)
        if result.get('screenshot_path')!=str(artifact) or result.get('bytes')!=artifact.stat().st_size or not artifact.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'):raise RuntimeError('native screenshot artifact mismatch')
        return result
    except BaseException:
        artifact.unlink(missing_ok=True);raise

if __name__=='__main__':start(int(os.environ.get('ABX_SERVER_PORT','9000')))
