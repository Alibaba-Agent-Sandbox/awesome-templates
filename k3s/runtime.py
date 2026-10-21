"""Owned ephemeral original agentless Kubernetes validation, without worker nodes."""
import fcntl,hashlib,importlib.util,json,os,re,stat,sys,tempfile,time
from pathlib import Path
BINARY=Path('/opt/k3s/k3s')
NODE_DIR=Path('/etc/rancher/node')
UPSTREAM=json.loads(Path(__file__).with_name('upstream.json').read_text())
IDENTITY=None
spec=importlib.util.spec_from_file_location('owned_k3s_process',Path(__file__).with_name('process.py'))
PROCESS=importlib.util.module_from_spec(spec);spec.loader.exec_module(PROCESS)

def executable():
    global IDENTITY
    try:info=BINARY.stat(follow_symlinks=False)
    except OSError:raise RuntimeError('original pinned K3s binary is unavailable')from None
    if BINARY.is_symlink()or not stat.S_ISREG(info.st_mode)or info.st_uid!=0 or info.st_mode&0o022 or info.st_size!=UPSTREAM['size']:raise RuntimeError('original K3s binary identity differs')
    current=(info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns,info.st_mode)
    if current!=IDENTITY:
        with BINARY.open('rb')as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=UPSTREAM['sha256']:raise RuntimeError('original K3s SHA256 differs')
        IDENTITY=current
    return str(BINARY)

def environment(private):
    return {'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':str(private),'TMPDIR':str(private),'LANG':'C.UTF-8','NO_COLOR':'1',
            'XDG_CACHE_HOME':str(private/'cache'),'XDG_CONFIG_HOME':str(private/'config')}

def diagnostic(arguments):
    with tempfile.TemporaryDirectory(prefix='abx-k3s-check-')as name:
        root=Path(name);root.chmod(0o700)
        config=root/'server-config.yaml';config.write_text('{}\n');config.chmod(0o600)
        argv=[executable(),*arguments]if arguments[0]!='server'else[executable(),'server','--config',str(config),*arguments[1:]]
        code,out,err=PROCESS.run(argv,cwd=root,env=environment(root),timeout=30)
    if code:raise RuntimeError('original K3s diagnostic failed; raw output omitted')
    return out.strip()

def setup():
    return {'mode':'original-k3s-agentless-validation','installed':BINARY.is_file(),'pinned_version':UPSTREAM['version'],
            'runtime_uid':os.geteuid(),'worker_nodes_supported':False,'pods_supported':False,'persistent_cluster':False,'node_state_empty':NODE_DIR.is_dir()and not NODE_DIR.is_symlink()and not list(NODE_DIR.iterdir())}

def cleanup_node_state(descriptor,started_ns):
    entries=os.listdir(descriptor)
    if not entries:return
    if entries!=['password']:raise RuntimeError('native node-state cleanup uncertain; foreign entries preserved')
    info=os.stat('password',dir_fd=descriptor,follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode)or info.st_uid!=os.geteuid()or info.st_size!=33 or info.st_ctime_ns<started_ns:raise RuntimeError('native node-state ownership differs; preserved')
    fd=os.open('password',os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=descriptor)
    with os.fdopen(fd,'rb')as stream:
        observed=os.fstat(stream.fileno());value=stream.read(34)
    if (observed.st_dev,observed.st_ino)!=(info.st_dev,info.st_ino)or not re.fullmatch(b'[0-9a-f]{32}\n',value):raise RuntimeError('native node-state identity differs; preserved')
    current=os.stat('password',dir_fd=descriptor,follow_symlinks=False)
    if (current.st_ino,current.st_ctime_ns,current.st_size)!=(info.st_ino,info.st_ctime_ns,info.st_size):raise RuntimeError('native node-state changed; preserved')
    os.unlink('password',dir_fd=descriptor)
    if os.listdir(descriptor):raise RuntimeError('native node-state cleanup absence unconfirmed')

def validate(manifest_yaml,command_timeout=180):
    if not isinstance(manifest_yaml,str)or not manifest_yaml.strip()or len(manifest_yaml.encode())>32768 or '\0'in manifest_yaml:raise ValueError('manifest_yaml must contain1..32768UTF8bytes without NUL')
    if type(command_timeout)is not int or not 30<=command_timeout<=300:raise ValueError('command_timeout must be integer30..300seconds')
    if os.geteuid()==0:raise RuntimeError('the reviewed K3s runtime must be non-root')
    try:descriptor=os.open(NODE_DIR,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
    except OSError:raise RuntimeError('reviewed private native node directory unavailable')from None
    try:
        info=os.fstat(descriptor)
        if info.st_uid!=os.geteuid()or info.st_mode&0o077:raise RuntimeError('reviewed private native node directory ownership differs')
        try:fcntl.flock(descriptor,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('another original K3s operation is active')from None
        if os.listdir(descriptor):raise RuntimeError('pre-existing native node state is preserved; use a fresh owned sandbox')
        started=time.time_ns()
        try:
            with tempfile.TemporaryDirectory(prefix='abx-k3s-validation-')as name:
                private=Path(name);private.chmod(0o700)
                manifest=private/'manifest.yaml';manifest.write_text(manifest_yaml);manifest.chmod(0o600)
                request=private/'request.json';request.write_text(json.dumps({'binary':executable(),'private':str(private),'manifest':str(manifest),'command_timeout':command_timeout,'node_dir':str(NODE_DIR)}));request.chmod(0o600)
                code,out,err=PROCESS.run([sys.executable,str(Path(__file__).with_name('worker.py')),str(request)],cwd=private,env=environment(private),timeout=command_timeout)
                if code:
                    try:diagnostic=json.loads(out)
                    except ValueError:diagnostic={}
                    if not diagnostic:
                        match=re.search(r'\b(ModuleNotFoundError|ImportError|PermissionError|FileNotFoundError|SyntaxError|RuntimeError)\b',err)
                        diagnostic={'stage':'worker_bootstrap','error_type':match[1]if match else'unknown'}
                    stage=diagnostic.get('stage','unknown')
                    if not isinstance(stage,str)or not re.fullmatch('[a-z_]{1,48}',stage):stage='unknown'
                    kind=diagnostic.get('error_type','unknown')
                    if not isinstance(kind,str)or not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,63}',kind):kind='unknown'
                    markers=diagnostic.get('native_log_markers',{})
                    flags=','.join(key for key,value in markers.items()if value is True and re.fullmatch('[a-z_]{1,32}',key))if isinstance(markers,dict)else''
                    metrics=diagnostic.get('native_metrics',{})
                    allowed=['native_stdout_bytes','native_stderr_bytes','native_was_running','native_config_created','native_elapsed_ms','native_exit_before_cleanup','native_oom_kills']
                    suffix=''.join('; '+key+'='+str(metrics[key])for key in allowed if isinstance(metrics,dict)and type(metrics.get(key))is int and -128<=metrics[key]<=8388608)
                    words=diagnostic.get('startup_words','')
                    if not isinstance(words,str)or len(words)>600 or not re.fullmatch('[a-z _-]*',words):words=''
                    suffix+='; startup_words='+words
                    raise RuntimeError('original agentless K3s failed; diagnostic_stage='+stage+'; diagnostic_type='+kind+'; native_markers='+flags+suffix+';')
                try:result=json.loads(out)
                except ValueError:raise RuntimeError('original K3s worker result is invalid; output omitted')from None
                required=['api_ready','post_api_ready','probe_not_persisted','api_server_stopped']
                if not isinstance(result,dict)or type(result.get('valid'))is not bool or any(result.get(k)is not True for k in required)or result.get('worker_nodes')!=0 or result.get('runtime_uid')!=os.geteuid():raise RuntimeError('original K3s completion/cleanup proof is incomplete')
        finally:cleanup_node_state(descriptor,started)
        result.update(private_state_removed=not private.exists(),node_state_restored=not os.listdir(descriptor),native_version=UPSTREAM['version'],native_sha256=UPSTREAM['sha256'],mode='original-k3s-agentless-validation')
        if not result['private_state_removed']or not result['node_state_restored']:raise RuntimeError('owned original K3s state absence unconfirmed')
        return result
    finally:os.close(descriptor)
