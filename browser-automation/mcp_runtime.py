"""Actual pinned Playwright MCP lifecycle and local JSON-RPC transport.

The standard MCP listener is private to the sandbox. Named calls use the shared
command server's authentication. No model, credential discovery or npx download.
"""
from __future__ import annotations
import atexit
import http.client
import importlib.metadata
import importlib.util
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

spec=importlib.util.spec_from_file_location('browser_mcp_process',Path(__file__).with_name('mcp_process.py'))
life=importlib.util.module_from_spec(spec);spec.loader.exec_module(life)
_SESSION={}
PORT=8931


def _installation():
    modules=Path(os.environ.get('MCP_NODE_MODULES','/opt/playwright-mcp/node_modules')).resolve(strict=True)
    pins={'@playwright/mcp':'0.0.83','playwright':'1.64.0-alpha-1790635538000','playwright-core':'1.64.0-alpha-1790635538000'}
    for package,version in pins.items():
        if json.loads((modules/package/'package.json').read_text())['version']!=version:
            raise RuntimeError('installed native MCP dependencies differ from pins')
    if importlib.metadata.version('playwright')!='1.58.0':
        raise RuntimeError('Python Playwright pin differs')
    browsers=Path(os.environ.get('PLAYWRIGHT_BROWSERS_PATH',str(Path.home()/'.cache/ms-playwright')))
    matches=list(browsers.glob('chromium-1208/chrome-linux64/chrome'))
    if len(matches)!=1 or not matches[0].is_file():
        raise RuntimeError('existing pinned Chromium1208 is required; no second browser download')
    node=shutil.which('node')
    if not node:raise RuntimeError('base Node runtime unavailable')
    return node,modules/'@playwright/mcp/cli.js',matches[0]


def _request(method,payload=None,timeout=30):
    connection=http.client.HTTPConnection('127.0.0.1',PORT,timeout=timeout)
    try:
        body=json.dumps(payload).encode() if payload is not None else None
        headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream'}|_SESSION.get('headers',{})
        connection.request(method,'/mcp',body,headers)
        response=connection.getresponse();data=response.read(4*1024**2+1)
        if len(data)>4*1024**2:raise RuntimeError('MCP response exceeds4MiB')
        if response.getheader('Mcp-Session-Id'):
            _SESSION.setdefault('headers',{})['Mcp-Session-Id']=response.getheader('Mcp-Session-Id')
        if response.status not in (200,202,204):raise RuntimeError('native MCP HTTP request failed')
        if not data:return None
        if response.getheader('Content-Type','').split(';')[0]=='text/event-stream':
            # One JSON-RPC response; ignore empty keepalive comments/events.
            events=data.decode().replace('\r\n','\n').split('\n\n')
            candidates=['\n'.join(line[5:].lstrip() for line in event.splitlines() if line.startswith('data:')) for event in events]
            values=[json.loads(value) for value in candidates if value]
            return next(value for value in values if value.get('id')==payload.get('id'))
        return json.loads(data)
    finally:connection.close()


def _rpc(method,params=None):
    _SESSION['sequence']=_SESSION.get('sequence',0)+1
    request={'jsonrpc':'2.0','id':_SESSION['sequence'],'method':method}
    if params is not None:request['params']=params
    response=_request('POST',request)
    if not isinstance(response,dict) or response.get('id')!=request['id'] or 'error' in response or 'result' not in response:
        raise RuntimeError('native MCP JSON-RPC response failed')
    return response['result']


def status():
    with life._LOCK:
        if not life._STATE:return {'running':False}
        if not life._alive(life._STATE['process']):stop();return {'running':False}
        return {'running':True,'port':PORT,'mcp_version':'0.0.83','protocol_version':_SESSION['protocol_version']}


def start():
    with life._LOCK:
        if life._STATE:raise RuntimeError('stop existing owned MCP before starting another')
        node,cli,browser=_installation()
        with socket.socket() as probe:
            probe.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            try:probe.bind(('0.0.0.0',PORT))
            except OSError:raise RuntimeError('MCP port already in use') from None
        private=tempfile.TemporaryDirectory(prefix='abx-browser-mcp-');root=Path(private.name);root.chmod(0o700)
        config=root/'config.json';config.write_text(json.dumps({'browser':{'browserName':'chromium','isolated':True,
            'launchOptions':{'executablePath':str(browser),'headless':True,'args':['--disable-dev-shm-usage']}},
            'webmcp':False,'outputDir':str(root/'output'),'timeouts':{'action':10000,'navigation':20000}}));config.chmod(0o600)
        owner=secrets.token_hex(16)
        env={'PATH':os.environ.get('PATH','/usr/local/bin:/usr/bin:/bin'),'HOME':str(root),'TMPDIR':str(root),
            'LANG':'C.UTF-8','ABX_BROWSER_MCP_OWNER':owner,'PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD':'1'}
        argv=[node,str(cli),'--config',str(config),'--host','127.0.0.1','--port',str(PORT),
            '--allowed-hosts','127.0.0.1:'+str(PORT),'--idle-timeout','60000','--output-max-size','10485760']
        try:process=subprocess.Popen(argv,cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
        except BaseException:private.cleanup();raise
        def drain():
            try:
                while process.stdout.read(65536):pass
            finally:process.stdout.close()
        reader=threading.Thread(target=drain,daemon=True)
        life._STATE.update(process=process,private=private,reader=reader,port=PORT,owner=owner,pidfds={});reader.start()
        try:
            deadline=time.monotonic()+30
            while True:
                if not life._alive(process):raise RuntimeError('native MCP exited before readiness')
                try:
                    initialized=_rpc('initialize',{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'agent-sandbox-browser','version':'2.1.0'}})
                    break
                except (OSError,http.client.HTTPException):
                    if time.monotonic()>=deadline:raise RuntimeError('native MCP startup deadline exceeded') from None
                    time.sleep(.1)
            _SESSION['protocol_version']=initialized['protocolVersion']
            _SESSION.setdefault('headers',{})['Mcp-Protocol-Version']=initialized['protocolVersion']
            _request('POST',{'jsonrpc':'2.0','method':'notifications/initialized'})
            names={tool['name'] for tool in _rpc('tools/list')['tools']}
            if not {'browser_navigate','browser_click','browser_snapshot','browser_take_screenshot'}<=names:
                raise RuntimeError('required actual MCP tools are missing')
            return status()
        except BaseException:stop();raise


def call(method,params_json='{}'):
    if method not in ['tools/list','tools/call','ping']:raise ValueError('method must be tools/list, tools/call or ping')
    if not isinstance(params_json,str) or len(params_json.encode())>65536:raise ValueError('params_json must be at most64KiB')
    try:params=json.loads(params_json)
    except ValueError:raise ValueError('params_json must encode an object') from None
    if not isinstance(params,dict):raise ValueError('params_json must encode an object')
    with life._LOCK:
        if not life._STATE or not life._alive(life._STATE['process']):raise RuntimeError('start the owned MCP server first')
        return _rpc(method,params)


def stop():
    with life._LOCK:
        if life._STATE:
            try:_request('DELETE',timeout=5)
            except Exception:pass
            life._stop()
        _SESSION.clear()
        return {'running':False}


atexit.register(stop)


def self_test():
    """Actual native tools, independent fixture state and a newly created PNG."""
    from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
    with life._LOCK:
        if life._STATE:raise RuntimeError('stop existing owned MCP before self-test')
        counter={'value':0};counter_lock=threading.Lock()
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                if self.path=='/increment':
                    with counter_lock:counter['value']+=1;data=str(counter['value']).encode()
                    kind='text/plain'
                else:
                    data=b'<html><title>ABX_MCP_COUNTER</title><body><p id="count">Count 0</p><button onclick="fetch(\'/increment\').then(r=>r.text()).then(n=>document.querySelector(\'#count\').textContent=\'Count \'+n)">Increment</button></body></html>';kind='text/html'
                self.send_response(200);self.send_header('Content-Type',kind);self.end_headers();self.wfile.write(data)
        fixture=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=fixture.serve_forever,daemon=True);thread.start()
        try:
            start()
            def tool(name,arguments):
                result=call('tools/call',json.dumps({'name':name,'arguments':arguments}))
                if result.get('isError'):raise RuntimeError('actual native MCP tool failed')
                return '\n'.join(part.get('text','') for part in result.get('content',[]))
            tool('browser_navigate',{'url':'http://127.0.0.1:'+str(fixture.server_port)+'/'})
            text=tool('browser_snapshot',{})
            if 'ABX_MCP_COUNTER' not in text or 'Count 0' not in text:raise RuntimeError('actual MCP fixture not rendered')
            match=re.search(r'button "Increment" \[ref=([^\]]+)\]',text)
            if not match:raise RuntimeError('actual MCP accessibility button target missing')
            for _ in range(2):tool('browser_click',{'element':'Increment','target':match[1]})
            for _ in range(20):
                if 'Count 2' in tool('browser_snapshot',{}):break
                time.sleep(.1)
            else:raise RuntimeError('actual MCP click did not update rendered DOM')
            with counter_lock:
                if counter['value']!=2:raise RuntimeError('independent HTTP fixture did not observe two browser clicks')
            root=Path(life._STATE['private'].name);picture=root/'owned-mcp-proof.png'
            if picture.exists():raise RuntimeError('refuse existing screenshot')
            tool('browser_take_screenshot',{'filename':picture.name})
            data=picture.read_bytes()
            if data[:16]!=b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR' or int.from_bytes(data[16:20],'big')<500 or int.from_bytes(data[20:24],'big')<300:
                raise RuntimeError('actual MCP screenshot PNG proof missing')
        finally:
            try:stop()
            finally:
                fixture.shutdown();fixture.server_close();thread.join(timeout=5)
                if thread.is_alive():raise RuntimeError('owned MCP fixture cleanup not confirmed')
        return 'PLAYWRIGHT_MCP_OK'
