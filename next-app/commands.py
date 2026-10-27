"""Pinned Next.js/Vite scaffolds and explicit owned development-server lifecycle."""
from __future__ import annotations
import atexit
import http.client
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import subprocess
import tempfile
import threading
import time
from agent_sandbox.server import command,start
import importlib.util
_life_spec=importlib.util.spec_from_file_location('next_app_lifecycle',Path(__file__).with_name('lifecycle.py'))
life=importlib.util.module_from_spec(_life_spec)
_life_spec.loader.exec_module(life)


def _tools():
    root=Path(os.environ.get('NEXT_APP_TOOLCHAIN','/opt/next-app')).resolve(strict=True)
    metadata=json.loads((root/'package.json').read_text())
    if metadata.get('dependencies',{})!={'next':'16.4.2','react':'19.3.1','react-dom':'19.3.1','vite':'8.3.4'}:
        raise RuntimeError('installed toolchain manifest differs from reviewed pins')
    return root


def _kind(kind):
    if kind not in ['next','vite']:raise ValueError('kind must be next or vite')


def _project(path):
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,62}',path):raise ValueError('path must be a single workspace directory name')
    base=Path(os.environ.get('WORKSPACE','/home/user/app')).resolve(strict=True)
    candidate=base/path
    if candidate.is_symlink():raise ValueError('project directory must not be a symlink')
    return candidate


@command('toolchain_versions',description='Inspect exact installed Next/React/Vite package versions without starting a development server.')
def toolchain_versions() -> dict:
    root=_tools();result={}
    for package in ['next','react','react-dom','vite']:
        result[package]=json.loads((root/'node_modules'/package/'package.json').read_text())['version']
    return result


@command('scaffold',description='Create a new owned minimal Next.js or Vite project; never overwrite an existing directory.')
def scaffold(kind: str='next',path: str='preview-app') -> dict:
    _kind(kind);project=_project(path);tools=_tools()
    project.mkdir(mode=0o700)
    try:
        files={'.abx-next-app.json':json.dumps({'kind':kind,'template_version':'1.1.4'}),
            'package.json':json.dumps({'name':'sandbox-preview','version':'1.0.0','private':True,'type':'module',
                'dependencies':json.loads((tools/'package.json').read_text())['dependencies']})}
        if kind=='next':
            files.update({'next.config.mjs':"export default {allowedDevOrigins: ['127.0.0.1']};\n",
                'app/layout.js':'export default function Layout({children}) { return <html><body>{children}</body></html>; }\n',
                'app/page.js':'export default function Page() { return <h1>ABX_NEXT_PREVIEW</h1>; }\n'})
        else:files['index.html']='<!doctype html><html><body><h1>ABX_VITE_PREVIEW</h1><script type="module" src="/main.js"></script></body></html>\n';files['main.js']='document.body.dataset.loaded="yes";\n'
        for name,content in files.items():
            target=project/name;target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('x') as stream:stream.write(content)
        (project/'node_modules').symlink_to(tools/'node_modules',target_is_directory=True)
    except BaseException:
        shutil.rmtree(project)
        raise
    return {'path':path,'kind':kind}


@command('dev_start',description='Start one owned pinned Next.js/Vite server with filtered environment and explicit readiness deadline.')
def dev_start(kind: str='next',path: str='preview-app',timeout_s: int=120,allowed_host: str='') -> dict:
    _kind(kind)
    if not isinstance(allowed_host,str) or (allowed_host and (kind!='vite' or len(allowed_host)>253 or any(not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?',label) for label in allowed_host.split('.')))):
        raise ValueError('allowed_host must be one exact Vite DNS hostname, without scheme, port or wildcard')
    if not 1<=timeout_s<=180:raise ValueError('timeout_s must be1..180')
    project=_project(path).resolve(strict=True)
    metadata=json.loads((project/'.abx-next-app.json').read_text())
    if metadata.get('kind')!=kind:raise ValueError('scaffold kind does not match')
    tools=_tools();port=3000 if kind=='next' else 5173
    if not hasattr(os,'pidfd_open'):raise RuntimeError('Linux pidfd ownership is required')
    with life._LOCK:
        if life._STATE.get('process') is not None:raise RuntimeError('stop the current owned server before starting another')
        with socket.socket() as listener:
            listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            try:listener.bind(('0.0.0.0',port))
            except OSError:raise RuntimeError('development port is already in use') from None
        private=tempfile.TemporaryDirectory(prefix='abx-next-app-');root=Path(private.name);root.chmod(0o700)
        env={'ABX_NEXT_APP_OWNER':secrets.token_hex(16),'HOME':str(root),'PATH':os.environ.get('PATH','/usr/local/bin:/usr/bin:/bin'),
            'LANG':'C.UTF-8','NEXT_TELEMETRY_DISABLED':'1','NODE_ENV':'development'}
        if allowed_host:env['__VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS']=allowed_host.lower()
        node=shutil.which('node')
        if not node:private.cleanup();raise RuntimeError('Node is unavailable')
        argv=([node,str(tools/'node_modules/next/dist/bin/next'),'dev','--webpack','--hostname','0.0.0.0','--port',str(port)] if kind=='next'
            else [node,str(tools/'node_modules/vite/bin/vite.js'),'--host','0.0.0.0','--port',str(port),'--strictPort'])
        try:process=subprocess.Popen(argv,cwd=project,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
        except BaseException:private.cleanup();raise
        retained=bytearray();logs_lock=threading.Lock()
        def drain():
            try:
                while block:=process.stdout.read1(8192):
                    with logs_lock:retained.extend(block);del retained[:-65536]
            finally:process.stdout.close()
        reader=threading.Thread(target=drain,daemon=True)
        life._STATE.update(process=process,private=private,reader=reader,port=port,owner=env['ABX_NEXT_APP_OWNER'],pidfds={},logs=retained,logs_lock=logs_lock,kind=kind,path=path)
        reader.start();deadline=time.monotonic()+timeout_s
        try:
            while time.monotonic()<deadline:
                if not life._alive(process):raise RuntimeError('development server exited before readiness')
                try:
                    status,_,content=life._request(port,'GET','/',timeout=min(1,max(.01,deadline-time.monotonic())))
                    marker=b'ABX_NEXT_PREVIEW' if kind=='next' else b'ABX_VITE_PREVIEW'
                    if status==200 and marker in content and life._alive(process):return {'port':port,'kind':kind,'running':True}
                except (OSError,http.client.HTTPException):pass
                time.sleep(.1)
            raise RuntimeError('development server readiness deadline exceeded')
        except BaseException:life._stop();raise


@command('dev_status',description='Inspect only the development server owned by this command-server process.')
def dev_status() -> dict:
    with life._LOCK:
        if not life._STATE:return {'running':False}
        if not life._alive(life._STATE['process']):life._stop();return {'running':False}
        return {k:life._STATE[k] for k in ['port','kind','path']}|{'running':True}


@command('dev_logs',description='Return up to8KiB of the owned development server log tail; output is buffered, not a streaming API.')
def dev_logs(tail_bytes: int=4096) -> str:
    if not 1<=tail_bytes<=8192:raise ValueError('tail_bytes must be1..8192')
    with life._LOCK:
        if not life._STATE:return ''
        with life._STATE['logs_lock']:return bytes(life._STATE['logs'])[-tail_bytes:].decode('utf-8','replace')


@command('dev_stop',description='Stop the owned process group and marked workers, verify listener absence and remove temporary state.')
def dev_stop() -> dict:
    with life._LOCK:life._stop();return {'running':False}


@command('preview_self_test',description='Start both actual pinned previews, fetch their marker pages, stop owned workers and remove nonce-owned projects.')
def preview_self_test() -> str:
    with life._LOCK:
        if life._STATE:raise RuntimeError('stop the existing owned server before self-test')
        for kind in ['next','vite']:
            name='abx_e2e_preview_'+secrets.token_hex(6);created=False
            try:
                scaffold(kind,name);created=True
                dev_start(kind,name)
            finally:
                if life._STATE.get('path')==name:dev_stop()
                if created:
                    project=_project(name);shutil.rmtree(project)
                    if project.exists():raise RuntimeError('owned preview project cleanup remains unconfirmed')
    return 'NEXT_VITE_PREVIEW_OK'


def _exit():
    with life._LOCK:life._stop()
atexit.register(_exit)
if __name__=='__main__':start(int(os.environ.get('ABX_SERVER_PORT','9000')))
