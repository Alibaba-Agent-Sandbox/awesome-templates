"""Private fixed worker; original server and kubectl operate only on its fresh state."""
import ipaddress,json,os,re,signal,socket,subprocess,sys,threading,time,uuid
from pathlib import Path
import process_rpc
import lifecycle
REPORT={'stage':'initialization'}
LOGS=[bytearray(),bytearray()]

def oom_kills():
    try:return int(dict(line.split()for line in Path('/sys/fs/cgroup/memory.events').read_text().splitlines()).get('oom_kill',0))
    except (OSError,ValueError):return None

def startup_words(logs):
    """Startup-only vocabulary; strip credentials, addresses, paths and opaque values."""
    lines=[]
    for line in b'\n'.join(logs).decode('utf-8','replace').splitlines()[-6:]:
        if re.search(r'token|password|secret|certificate|private.key',line,re.I):continue
        line=re.sub(r'https?://\S+|/[\w./:+@%=-]+',' redacted ',line)
        line=re.sub(r'\b[\w-]*[0-9][\w.-]*\b',' redacted ',line)
        line=re.sub(r'[^a-zA-Z _-]+',' ',line)
        lines.append(' '.join(line.lower().split()))
    return ' '.join(lines)[-600:]

def alive(process):return os.waitid(os.P_PID,process.pid,os.WEXITED|os.WNOHANG|os.WNOWAIT)is None

def address():
    # Route selection only: UDP connect sends no application packet.
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM)as probe:
        probe.connect(('192.0.2.1',9));value=probe.getsockname()[0]
    ip=ipaddress.ip_address(value)
    if ip.is_loopback or ip.is_unspecified:raise RuntimeError('non-loopback owned guest address unavailable')
    return value

def run(request):
    private=Path(request['private']);binary=request['binary'];manifest=Path(request['manifest']);config=private/'kubeconfig.yaml'
    began=time.monotonic();oom_before=oom_kills()
    deadline=began+request['command_timeout']-12
    env=dict(os.environ)
    with socket.socket()as reservation:reservation.bind(('127.0.0.1',0));port=reservation.getsockname()[1]
    native_config=private/'server-config.yaml';native_config.write_text('{}\n');native_config.chmod(0o600)
    REPORT['stage']='server_start'
    argv=[binary,'server','--config',str(native_config),'--disable-agent','--data-dir',str(private/'data'),'--write-kubeconfig',str(config),'--https-listen-port',str(port),'--bind-address','0.0.0.0','--advertise-address',address()]
    for name in ['coredns','traefik','servicelb','metrics-server','local-storage']:argv+=['--disable',name]
    server=subprocess.Popen(argv,cwd=private,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    overflow=threading.Event();readers=[]
    def drain(stream,buffer,key):
        total=0
        try:
            while chunk:=stream.read(8192):
                total+=len(chunk);REPORT[key]=total;buffer.extend(chunk)
                if len(buffer)>65536:del buffer[:-65536]
                if total>2*1024**2:overflow.set()
        finally:stream.close()
    for stream,buffer,key in zip([server.stdout,server.stderr],LOGS,['native_stdout_bytes','native_stderr_bytes']):
        thread=threading.Thread(target=drain,args=(stream,buffer,key),daemon=True);thread.start();readers.append(thread)
    def rpc(arguments,seconds=10):
        remaining=deadline-time.monotonic()
        if remaining<=0 or overflow.is_set()or not alive(server):raise RuntimeError('owned original server unavailable or deadline/log bound exceeded')
        return process_rpc.run([binary,'kubectl','--kubeconfig',str(config),'--request-timeout=5s',*arguments],cwd=private,env=env,timeout=min(seconds,remaining))
    def require(arguments):
        code,out,err=rpc(arguments)
        if code:raise RuntimeError('owned original Kubernetes API request failed')
        return out
    def absent(name):
        code,out,err=rpc(['get','namespace',name,'-o','json'])
        if code!=1 or 'notfound'not in err.lower()or name not in err:raise RuntimeError('owned probe namespace absence unconfirmed')
    result=None
    try:
        REPORT['stage']='readiness'
        ready=False
        while time.monotonic()<deadline:
            if config.exists():
                code,out,err=rpc(['get','--raw','/readyz'],seconds=6)
                if code==0 and out.strip()=='ok':ready=True;break
            if not alive(server)or overflow.is_set():break
            time.sleep(.3)
        if not ready:raise RuntimeError('original agentless Kubernetes API did not become ready')
        REPORT['stage']='node_baseline'
        nodes=json.loads(require(['get','nodes','-o','json']))
        if nodes.get('items')!=[]:raise RuntimeError('unexpected worker nodes in agentless profile')
        REPORT['stage']='probe_dry_run'
        probe='abx-probe-'+uuid.uuid4().hex
        created=json.loads(require(['create','namespace',probe,'--dry-run=server','-o','json']))
        if created.get('kind')!='Namespace'or created.get('metadata',{}).get('name')!=probe:raise RuntimeError('original server dry-run identity differs')
        absent(probe)
        REPORT['stage']='manifest_validation'
        code,out,err=rpc(['apply','--dry-run=server','--validate=strict','-f',str(manifest),'-o','json'],seconds=30)
        result={'valid':code==0,'runtime_uid':os.geteuid(),'api_ready':True,'worker_nodes':0}
        if code==0:
            value=json.loads(out)
            if not isinstance(value,dict)or not value.get('kind'):raise RuntimeError('original dry-run response is not a Kubernetes object')
            result['object']=value;result['validation_error']=''
        else:
            text=err.lower()
            infrastructure=['connection refused','unable to connect','failed to download','deadline exceeded','i/o timeout','tls handshake','unexpected eof','no route to host','certificate signed by unknown']
            validation=['error validating data','strict decoding error','is invalid:','error parsing','error converting yaml to json','unable to decode','no matches for kind']
            schema_decode='error from server (badrequest)'in text and any(value in text for value in ['cannot unmarshal','cannot be handled as a'])
            if code!=1 or any(value in text for value in infrastructure)or not(any(value in text for value in validation)or schema_decode):raise RuntimeError('original validation failed with an unclassified infrastructure/native error')
            result['object']=None;result['validation_error']=err.replace(str(private),'[OWNED_STATE]')[:4096]
        REPORT['stage']='post_validation'
        if require(['get','--raw','/readyz']).strip()!='ok':raise RuntimeError('original API post-validation readiness differs')
        if json.loads(require(['get','nodes','-o','json'])).get('items')!=[]:raise RuntimeError('unexpected worker nodes after validation')
        absent(probe);result.update(post_api_ready=True,probe_not_persisted=True)
    finally:
        REPORT['operation_stage']=REPORT['stage'];REPORT['stage']='server_cleanup'
        REPORT['native_was_running']=int(alive(server));REPORT['native_config_created']=int(config.exists())
        REPORT['native_elapsed_ms']=int((time.monotonic()-began)*1000)
        if not REPORT['native_was_running']:
            status=os.waitid(os.P_PID,server.pid,os.WEXITED|os.WNOHANG|os.WNOWAIT)
            REPORT['native_exit_before_cleanup']=status.si_status if status.si_code==os.CLD_EXITED else -status.si_status
        oom_after=oom_kills()
        if oom_before is not None and oom_after is not None:REPORT['native_oom_kills']=max(0,oom_after-oom_before)
        try:os.killpg(server.pid,signal.SIGTERM)
        except ProcessLookupError:pass
        limit=time.monotonic()+2
        while alive(server)and time.monotonic()<limit:time.sleep(.02)
        try:os.killpg(server.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        server.wait(timeout=5)
        for thread in readers:thread.join(timeout=2)
        listening=lifecycle._listener_exists(port)
        if listening or any(thread.is_alive()for thread in readers):raise RuntimeError('owned original server/listener cleanup unconfirmed')
    result['api_server_stopped']=True
    return result

if __name__=='__main__':
    try:
        request=json.loads(Path(sys.argv[1]).read_text());print(json.dumps(run(request)),flush=True)
    except Exception as exc:
        text=b'\n'.join(LOGS).lower()
        markers={name:word in text for name,word in [('permission',b'permission denied'),('namespace',b'operation not permitted'),('root',b'root'),('ip_forward',b'ip_forward'),('cgroup',b'cgroup'),('advertise',b'advertise'),('unknown_flag',b'flag provided but not defined'),('panic',b'panic:'),('bind',b'address already in use')]}
        print(json.dumps({'error_type':type(exc).__name__,'stage':REPORT.get('operation_stage',REPORT['stage']),'native_log_markers':markers,'startup_words':startup_words(LOGS)if REPORT.get('native_config_created')==0 else'','native_metrics':{key:value for key,value in REPORT.items()if key.startswith('native_')and type(value)is int}}),flush=True)
        raise SystemExit(1)
