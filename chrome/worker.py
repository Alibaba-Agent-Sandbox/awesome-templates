"""Owned genuine headed Chrome/X11/VNC session; JSON IPC only on stdout."""
import asyncio,base64,contextlib,io,json,os,secrets,signal,socket,string,subprocess,sys,time,urllib.request
from pathlib import Path
from urllib.parse import quote
from cdp import Page
from native import browser
from rfb import capture_tcp

STATE=Path(sys.argv[1])if __name__=='__main__'else None


class InitializationError(RuntimeError):
    def __init__(self,stage,cause):self.stage=stage;self.cause=cause;super().__init__('native Chrome initialization failed')


def available(port):
    try:
        with socket.create_connection(('127.0.0.1',port),timeout=.15):return True
    except OSError:return False


class Desktop:
    def __init__(self,root):
        self.root=root;self.children=[];self.stage='initialization';self.display_info=None
        self.password=''.join(secrets.choice(string.ascii_letters+string.digits)for _ in range(8))
        self.base_env={k:os.environ[k]for k in ['ABX_CHROME_OWNER','LANG','LC_ALL']if k in os.environ}
        self.base_env.update(PATH='/usr/local/bin:/usr/bin:/bin',HOME=str(root),TMPDIR=str(root),
            XDG_CACHE_HOME=str(root/'cache'),XDG_CONFIG_HOME=str(root/'config'),XDG_DATA_HOME=str(root/'data'),
            XDG_RUNTIME_DIR=str(root/'runtime'),PYTHONNOUSERSITE='1',PYTHONUNBUFFERED='1',NO_COLOR='1')
        (root/'runtime').mkdir(mode=0o700)
        try:self.start()
        except Exception as exc:self.close();raise InitializationError(self.stage,type(exc).__name__)from None
        except BaseException:self.close();raise

    def spawn(self,argv,env=None):
        process=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
            env=self.base_env if env is None else env,cwd=self.root)
        self.children.append(process);return process

    def start(self):
        self.stage='native_integrity';binary,self.provenance=browser()
        self.stage='display'
        for _ in range(100):
            number=1000+secrets.randbelow(50000)
            if not Path(f'/tmp/.X{number}-lock').exists()and not Path(f'/tmp/.X11-unix/X{number}').exists():break
        else:raise RuntimeError('no unused X display')
        self.base_env.update(DISPLAY=':'+str(number),XAUTHORITY=str(self.root/'Xauthority'))
        subprocess.run(['/usr/bin/xauth','-f',self.base_env['XAUTHORITY'],'source','-'],
            input=('add :'+str(number)+' MIT-MAGIC-COOKIE-1 '+secrets.token_hex(16)+'\n').encode(),
            env=self.base_env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5,check=True)
        Path(self.base_env['XAUTHORITY']).chmod(0o600)
        xvfb=self.spawn(['/usr/bin/Xvfb',':'+str(number),'-screen','0','1024x768x24','-nolisten','tcp','-auth',self.base_env['XAUTHORITY']])
        for _ in range(100):
            if Path(f'/tmp/.X11-unix/X{number}').exists():break
            if xvfb.poll()is not None:raise RuntimeError('owned Xvfb exited')
            time.sleep(.05)
        else:raise RuntimeError('owned X display deadline')
        socket_path=Path(f'/tmp/.X11-unix/X{number}');lock=Path(f'/tmp/.X{number}-lock')
        self.display_info={'number':number,'pid':xvfb.pid,'socket_inode':socket_path.stat().st_ino,
            'lock_inode':lock.stat().st_ino if lock.exists()else None}
        (self.root/'display.json').write_text(json.dumps(self.display_info))
        self.stage='window_manager'
        config=self.root/'openbox.xml';config.write_text('<openbox_config xmlns="http://openbox.org/3.4/rc"><applications><application class="*"><decor>no</decor></application></applications></openbox_config>')
        manager=self.spawn(['/usr/bin/openbox','--sm-disable','--config-file',str(config)])
        for _ in range(100):
            result=subprocess.run(['/usr/bin/xprop','-root','_NET_SUPPORTING_WM_CHECK'],env=self.base_env,capture_output=True,timeout=3)
            if result.returncode==0 and b'window id'in result.stdout:break
            if manager.poll()is not None:raise RuntimeError('owned window manager exited')
            time.sleep(.05)
        else:raise RuntimeError('owned window manager deadline')
        self.stage='native_browser'
        self.chrome=self.spawn([binary,'--no-sandbox','--disable-dev-shm-usage','--disable-gpu',
            '--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-component-update',
            '--disable-sync','--disable-breakpad','--disable-domain-reliability','--metrics-recording-only',
            '--password-store=basic','--use-mock-keychain','--start-maximized','--window-size=1024,768',
            '--window-position=0,0','--remote-debugging-address=127.0.0.1','--remote-debugging-port=9223',
            '--user-data-dir='+str(self.root/'profile'),'about:blank'])
        for _ in range(200):
            try:
                with urllib.request.urlopen('http://127.0.0.1:9223/json/version',timeout=.5)as response:
                    value=json.load(response)
                if '145.0.7632.6'in value.get('Browser',''):break
            except (OSError,ValueError):pass
            if self.chrome.poll()is not None:raise RuntimeError('owned native Chrome exited')
            time.sleep(.1)
        else:raise RuntimeError('owned native Chrome deadline')
        self.stage='vnc'
        result=subprocess.run(['/usr/bin/tigervncpasswd','-f'],input=(self.password+'\n').encode(),
            env=self.base_env,capture_output=True,timeout=5,check=True)
        if len(result.stdout)!=8:raise RuntimeError('native VNC credential generation failed')
        password_file=self.root/'vnc.pass';password_file.write_bytes(result.stdout);password_file.chmod(0o600)
        self.vnc=self.spawn(['/usr/bin/x11vnc','-display',self.base_env['DISPLAY'],'-auth',self.base_env['XAUTHORITY'],
            '-rfbauth',str(password_file),'-rfbport','5901','-localhost','-forever','-shared','-noxdamage','-quiet'])
        self.stage='relay';env=dict(self.base_env)
        if os.environ.get('ABX_SERVER_TOKEN'):env['ABX_SERVER_TOKEN']=os.environ['ABX_SERVER_TOKEN']
        self.relay=self.spawn(['/opt/chrome/bin/python',str(Path(__file__).with_name('relay.py'))],env=env)
        for _ in range(100):
            if all(available(port)for port in [5901,9222,6080]):break
            if self.vnc.poll()is not None or self.relay.poll()is not None:raise RuntimeError('owned VNC/relay exited')
            time.sleep(.1)
        else:raise RuntimeError('owned VNC/relay deadline')
        self.stage='ready'

    def info(self):
        def metric(path):
            try:return Path(path).read_text().strip()
            except OSError:return None
        return {'running':all(p.poll()is None for p in self.children),'browser_version':'145.0.7632.6',
            'cdp':9222,'vnc':6080,'vnc_path':'/vnc.html','vnc_password':self.password,
            'width':1024,'height':768,'headed':True,'shm_bytes':os.statvfs('/dev/shm').f_blocks*os.statvfs('/dev/shm').f_frsize,
            'memory_limit':metric('/sys/fs/cgroup/memory.max'),
            'cpu_quota':metric('/sys/fs/cgroup/cpu.max'),'_owned_display':self.display_info}

    async def open(self,url):
        async with Page('http://127.0.0.1:9223')as page:
            value=await page.navigate(url)
            return {'url':value['url'],'title':value['title']}

    def screenshot(self):
        raw,width,height=asyncio.run(capture_tcp(5901,self.password))
        if len(raw)>8*1024*1024:raise RuntimeError('native screenshot exceeds8MiB')
        return {'content_base64':base64.b64encode(raw).decode(),'width':width,'height':height}

    async def smoke(self):
        self.stage="smoke_cdp"
        from PIL import Image
        marker='CHROME_NATIVE_'+secrets.token_hex(8)
        html='<html><head><title>'+marker+'</title></head><body style="margin:0;background:rgb(20,30,40)"><button style="position:absolute;left:30px;top:180px;width:160px;height:60px" onclick="document.body.style.background=\'rgb(10,230,20)\';this.textContent=\'native clicked\'">click</button></body></html>'
        async with Page('http://127.0.0.1:9223')as page:
            self.stage='smoke_navigate';await page.navigate('data:text/html,'+quote(html))
            self.stage='smoke_title'
            if await page.evaluate('document.title')!=marker:raise RuntimeError('native CDP title differs')
            self.stage='smoke_click';await page.evaluate('document.querySelector("button").click()')
        self.stage='smoke_vnc'
        for _ in range(20):
            raw,width,height=await capture_tcp(5901,self.password)
            image=Image.open(io.BytesIO(raw));pixel=image.getpixel((width//2,height//2))
            if pixel[1]>180 and pixel[0]<60 and pixel[2]<70:return {'native_cdp':True,'authenticated_vnc':True,'native_png':True,'headed':True}
            await asyncio.sleep(.1)
        self.stage='smoke_frame';self.frame_pixel=list(pixel[:3])
        raise RuntimeError('native VNC framebuffer does not show actual CDP state')

    def close(self):
        for process in reversed(self.children):
            if process.poll()is None:
                process.terminate()
                try:process.wait(timeout=2)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)


if __name__=='__main__':
    desktop=None
    signal.signal(signal.SIGTERM,lambda *_:sys.exit(0))
    try:
        desktop=Desktop(STATE);print(json.dumps({'result':desktop.info()}),flush=True)
        for line in sys.stdin:
            try:
                if len(line.encode())>32768:raise ValueError('IPC request exceeds32KiB')
                data=json.loads(line);operation=data['operation']
                if operation=='shutdown':print(json.dumps({'result':{'stopping':True}}),flush=True);break
                if operation=='status':result=desktop.info()
                elif operation=='open':result=asyncio.run(desktop.open(data['url']))
                elif operation=='screenshot':result=desktop.screenshot()
                elif operation=='smoke':result=asyncio.run(desktop.smoke())
                else:raise ValueError('unknown native Chrome operation')
                print(json.dumps({'result':result}),flush=True)
            except Exception as exc:
                reasons={'RFB3.8 required':'rfb_protocol','native VNC authentication failed':'rfb_auth','native VNC password authentication required':'rfb_security','invalid or oversized raw RFB rectangle':'rfb_rectangle','unsupported native RFB server message':'rfb_message','native CDP command failed':'cdp_command','native CDP stream closed':'cdp_closed','native browser evaluation failed':'cdp_evaluate','native browser navigation failed':'cdp_navigation','native browser navigation deadline exceeded':'cdp_navigation_deadline','native VNC framebuffer does not show actual CDP state':'frame_mismatch'}
                print(json.dumps({'error':True,'stage':desktop.stage,'error_type':type(exc).__name__,'reason':reasons.get(str(exc),'unclassified'),'frame_pixel':getattr(desktop,'frame_pixel',None)}),flush=True)
    except Exception as exc:
        print(json.dumps({'error':True,'stage':getattr(exc,'stage',desktop.stage if desktop else'initialization'),'error_type':getattr(exc,'cause',type(exc).__name__)}),flush=True)
    finally:
        if desktop is not None:desktop.close()
