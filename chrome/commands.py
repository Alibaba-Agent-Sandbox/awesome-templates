"""Named commands owning a genuine headed Chrome/CDP/noVNC session."""
import atexit,base64,hashlib,importlib.util,json,os,re,secrets,select,shutil,subprocess,tempfile,threading,time
from pathlib import Path
from urllib.parse import urlsplit
from agent_sandbox.server import command,start

ROOT=Path(os.environ.get('WORKSPACE','/home/user/workspace')).resolve()
LOCK=threading.RLock();PROCESS=None;PRIVATE=None;BUFFER=b'';INFO={}


def load(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


LIFE=load('chrome_owned_service_lifecycle','lifecycle.py')
RUNNER=load('chrome_owned_process_runner','process.py')
NATIVE=load('chrome_readonly_native','native.py')


def ports_absent():return not any(LIFE._listener_exists(port)for port in [9222,9223,5901,6080])


def environment(private):
    env={k:os.environ[k]for k in ['SSL_CERT_FILE','SSL_CERT_DIR']if k in os.environ}
    env.update(PATH='/usr/local/bin:/usr/bin:/bin',HOME=str(private),TMPDIR=str(private),
        WORKSPACE=str(ROOT),LANG='C.UTF-8',PYTHONUNBUFFERED='1',PYTHONNOUSERSITE='1')
    return env


def alive():
    try:return PROCESS is not None and LIFE._alive(PROCESS)
    except ChildProcessError:return False


def display_record():
    if PRIVATE is None:return None
    path=Path(PRIVATE.name)/'display.json'
    try:return json.loads(path.read_text())
    except (OSError,ValueError):return None


def remove_owned_display(value):
    if not value:return True
    number=value.get('number');pid=value.get('pid')
    if type(number)is not int or type(pid)is not int:return False
    socket=Path(f'/tmp/.X11-unix/X{number}');lock=Path(f'/tmp/.X{number}-lock')
    # Initial absence and exact socket/lock inode plus original pid prevent
    # deleting an unrelated replacement display after shutdown.
    if socket.exists()or lock.exists():
        try:
            if lock.exists()and lock.stat().st_uid!=os.getuid():return False
            if socket.exists()and socket.stat().st_uid!=os.getuid():return False
            if lock.exists()and(lock.stat().st_ino!=value['lock_inode']or int(lock.read_text().strip())!=pid):return False
            if socket.exists()and socket.stat().st_ino!=value['socket_inode']:return False
            socket.unlink(missing_ok=True);lock.unlink(missing_ok=True)
        except (OSError,ValueError,KeyError):return False
    return not socket.exists()and not lock.exists()


def stop_owned():
    global PROCESS,PRIVATE,BUFFER,INFO
    display=display_record()or INFO.get('_owned_display')
    if PROCESS is not None:
        LIFE._stop()
        for stream in [PROCESS.stdin,PROCESS.stdout,PROCESS.stderr]:
            if stream is not None:stream.close()
    elif PRIVATE is not None:PRIVATE.cleanup()
    display_absent=remove_owned_display(display)
    deadline=time.monotonic()+3
    while not ports_absent()and time.monotonic()<deadline:time.sleep(.02)
    if not display_absent or not ports_absent():
        remaining=','.join(str(port)for port in [9222,9223,5901,6080]if LIFE._listener_exists(port))
        raise RuntimeError('owned Chrome cleanup not confirmed: display='+str(display_absent)+'; ports='+remaining)
    PROCESS=None;PRIVATE=None;BUFFER=b'';INFO={}


def response(timeout):
    global BUFFER
    deadline=time.monotonic()+timeout
    try:
        while b'\n'not in BUFFER:
            remaining=deadline-time.monotonic()
            if remaining<=0 or not select.select([PROCESS.stdout],[],[],remaining)[0]:raise RuntimeError('native Chrome IPC deadline exceeded')
            part=os.read(PROCESS.stdout.fileno(),65536)
            if not part:raise RuntimeError('native Chrome worker exited')
            BUFFER+=part
            if len(BUFFER)>8*1024*1024:raise RuntimeError('native Chrome IPC output exceeds8MiB')
        line,BUFFER=BUFFER.split(b'\n',1);value=json.loads(line)
        if value.get('error'):
            stage=value.get('stage','native');kind=value.get('error_type','RuntimeError')
            if not re.fullmatch(r'[A-Za-z_]{1,40}',str(stage)+str(kind)):stage,kind='native','RuntimeError'
            reason=value.get('reason','unclassified')
            if not re.fullmatch(r'[a-z_]{1,40}',str(reason)):reason='unclassified'
            pixel=value.get('frame_pixel');observation=''
            if isinstance(pixel,list)and len(pixel)==3 and all(type(x)is int and 0<=x<=255 for x in pixel):observation=' RGB'+str(tuple(pixel))
            raise RuntimeError('native Chrome operation failed: '+stage+' ('+kind+') '+reason+observation)
        return value['result']
    except BaseException:
        stop_owned();raise


def request(operation,timeout=45,**parameters):
    if not alive():stop_owned();raise RuntimeError('Chrome is not running; call chrome_start')
    data=(json.dumps({'operation':operation,**parameters})+'\n').encode()
    if len(data)>32768:raise ValueError('native Chrome request exceeds32KiB')
    descriptor=PROCESS.stdin.fileno();os.set_blocking(descriptor,False);pending=memoryview(data);deadline=time.monotonic()+timeout
    try:
        while pending:
            remaining=deadline-time.monotonic()
            if remaining<=0 or not select.select([],[descriptor],[],remaining)[1]:raise RuntimeError('native Chrome IPC write deadline')
            try:pending=pending[os.write(descriptor,pending):]
            except BlockingIOError:continue
        return response(max(.1,deadline-time.monotonic()))
    except BaseException:stop_owned();raise


@command('chrome_version',description='Verify and report the actual pinned headed Chrome binary/version without a desktop session.')
def chrome_version() -> dict:
    binary,provenance=NATIVE.browser()
    with tempfile.TemporaryDirectory(prefix='abx-chrome-version-')as value:
        code,out,err=RUNNER.run([binary,'--version'],cwd=value,env=environment(Path(value)),timeout=30)
    if code or not re.search(r'\b145\.0\.7632\.6\b',out):raise RuntimeError('actual native Chrome version differs')
    return {'browser_version':'145.0.7632.6','native_binary_sha256':provenance['binary_sha256']}


@command('chrome_setup_check',description='Read-only native desktop installation and session availability; no browser launch.')
def chrome_setup_check() -> dict:
    paths=['/usr/bin/Xvfb','/usr/bin/openbox','/usr/bin/xauth','/usr/bin/x11vnc','/usr/bin/tigervncpasswd','/usr/bin/xprop','/opt/chrome/bin/python','/opt/chrome/browser-info.json','/usr/share/novnc/vnc.html']
    return {'installed':all(Path(path).is_file()for path in paths),'browser_version':'145.0.7632.6',
        'running':alive(),'reserved_ports_available':ports_absent(),'mode':'native-headed-cdp-vnc'}


@command('chrome_start',description='Start one owned genuine headed Chrome desktop; return CDP/noVNC ports and its generated temporary VNC password.')
def chrome_start() -> dict:
    global PROCESS,PRIVATE,INFO
    with LOCK:
        if alive():
            status=request('status')
            if status.get('running'):return {k:v for k,v in status.items()if not k.startswith('_')}|{'reused':True}
        stop_owned()
        if not ports_absent():raise RuntimeError('reserved browser ports already occupied')
        if not chrome_setup_check()['installed']:raise RuntimeError('native Chrome desktop runtime unavailable')
        if not ROOT.is_dir():raise ValueError('WORKSPACE must exist')
        NATIVE.browser();PRIVATE=tempfile.TemporaryDirectory(prefix='abx-chrome-session-');private=Path(PRIVATE.name);private.chmod(0o700)
        env=environment(private);owner=secrets.token_hex(16);env['ABX_CHROME_OWNER']=owner
        if os.environ.get('ABX_SERVER_TOKEN'):env['ABX_SERVER_TOKEN']=os.environ['ABX_SERVER_TOKEN']
        try:
            PROCESS=subprocess.Popen(['/opt/chrome/bin/python',str(Path(__file__).with_name('worker.py')),str(private)],
                env=env,cwd=private,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
            def discard():
                while PROCESS.stderr.read(65536):pass
            reader=threading.Thread(target=discard,daemon=True);reader.start()
            LIFE._STATE.update(process=PROCESS,private=PRIVATE,reader=reader,port=0,owner=owner,pidfds={})
            INFO=response(90)
            if INFO.get('running')is not True:raise RuntimeError('native Chrome session not ready')
            return {k:v for k,v in INFO.items()if not k.startswith('_')}|{'reused':False}
        except BaseException:stop_owned();raise


@command('chrome_status',description='Read actual owned native session status without starting or adopting a desktop.')
def chrome_status() -> dict:
    with LOCK:
        if not alive():return {'running':False,'owned_ports_absent':ports_absent(),'private_state_absent':PRIVATE is None}
        value=request('status')
        return {k:v for k,v in value.items()if not k.startswith('_')and k!='vnc_password'}


@command('chrome_open',description='Navigate the actual visible Chrome page to bounded HTTP(S) or about:blank; return final URL/title.')
def chrome_open(url: str='about:blank') -> dict:
    if not isinstance(url,str)or not url or len(url)>2048 or any(c.isspace()or ord(c)<32 for c in url):raise ValueError('invalid bounded browser URL')
    value=urlsplit(url)
    try:value.port
    except ValueError:raise ValueError('invalid browser URL port')from None
    if url!='about:blank'and(value.scheme not in ['https','http']or not value.hostname or value.username is not None or value.password is not None):raise ValueError('only HTTP(S) without embedded credentials or about:blank')
    with LOCK:return request('open',url=url)


@command('chrome_screenshot',description='Capture the real authenticated VNC desktop as a new exclusive workspace PNG and return path/bytes/SHA256.')
def chrome_screenshot() -> dict:
    with LOCK:
        value=request('screenshot');raw=base64.b64decode(value['content_base64'],validate=True)
        if len(raw)>8*1024*1024 or not raw.startswith(b'\x89PNG\r\n\x1a\n'):raise RuntimeError('native VNC did not return bounded PNG')
        path=ROOT/('abx_chrome_capture_'+secrets.token_hex(16)+'.png')
        descriptor=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        try:
            with os.fdopen(descriptor,'wb')as stream:stream.write(raw)
        except BaseException:path.unlink(missing_ok=True);raise
        return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'width':value['width'],'height':value['height']}


@command('chrome_stop',description='Stop only owned native browser/desktop/relay descendants, private state and display/ports.')
def chrome_stop() -> dict:
    with LOCK:
        stop_owned();return {'running':False,'owned_ports_absent':True,'private_state_absent':True}


@command('chrome_smoke',description='Exercise genuine headed CDP state and authenticated native VNC/PNG, then independently clean the owned session.')
def chrome_smoke() -> str:
    with LOCK:
        if alive():raise RuntimeError('smoke requires no active caller-owned browser session')
        try:
            chrome_start();value=request('smoke',timeout=60)
            if not all(value.get(k)is True for k in ['native_cdp','authenticated_vnc','native_png','headed']):raise RuntimeError('native Chrome CDP/VNC smoke incomplete')
        finally:chrome_stop()
        return 'native headed Chrome145.0.7632.6 CDP/VNC/PNG and cleanup OK'


atexit.register(lambda:stop_owned()if PROCESS is not None else None)
if __name__=='__main__':start(int(os.environ.get('ABX_SERVER_PORT','9000')))
