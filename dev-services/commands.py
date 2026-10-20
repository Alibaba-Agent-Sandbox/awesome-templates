"""Non-root PostgreSQL/Redis lifecycle without Docker or systemd."""
from __future__ import annotations
import atexit
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
from agent_sandbox.server import command,start


def _lifecycle(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name('lifecycle.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
_PG=_lifecycle('dev_services_postgres')
_REDIS=_lifecycle('dev_services_redis')
_LOCK=threading.RLock()
_SESSION={}


def _environment(private):
    env={'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':str(private),'LANG':'C.UTF-8','LC_ALL':'C.UTF-8'}
    if os.environ.get('DEV_SERVICES_LIBRARY_PATH'):env['LD_LIBRARY_PATH']=os.environ['DEV_SERVICES_LIBRARY_PATH']
    return env


def _binary(name):
    folder=Path(os.environ.get('DEV_SERVICES_POSTGRES_BIN','/usr/lib/postgresql/17/bin') if name in ['postgres','initdb','psql'] else os.environ.get('DEV_SERVICES_REDIS_BIN','/usr/bin'))
    candidate=folder/name
    if not candidate.is_file() or not os.access(candidate,os.X_OK):raise RuntimeError('pinned service executable is unavailable')
    return str(candidate)


def _data(path):
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,62}',path):raise ValueError('data_dir must be a single workspace directory name')
    base=Path(os.environ.get('WORKSPACE','/home/user/app')).resolve(strict=True);candidate=base/path
    if candidate.is_symlink():raise ValueError('data_dir must not be a symlink')
    return candidate


def _ports(postgres_port=0,redis_port=0):
    result=[]
    for value,key,fallback in [(postgres_port,'DEV_SERVICES_POSTGRES_PORT',5432),(redis_port,'DEV_SERVICES_REDIS_PORT',6379)]:
        if type(value) is not int:raise ValueError('database ports must be integers')
        if value==0:
            raw=os.environ.get(key,str(fallback))
            if not re.fullmatch(r'[0-9]{1,5}',raw):raise ValueError('configured database port must be numeric')
            value=int(raw)
        if not 1024<=value<=65535 or value==9000:raise ValueError('database ports must be1024..65535 excluding command port9000')
        result.append(value)
    if result[0]==result[1]:raise ValueError('database ports must differ')
    return tuple(result)


def _run(argv,private,env=None,timeout=30):
    code,stdout,_=_PG._run_process(argv,cwd=str(private),env=env or _environment(private),timeout=timeout)
    if code:raise RuntimeError(Path(argv[0]).name+' failed with exit'+str(code)+'; diagnostics omitted')
    return stdout.strip()


@command('services_setup_check',description='Read-only executable availability and configuration flags; no credential value or runtime acceptance claim.')
def services_setup_check() -> dict:
    try:
        for name in ['postgres','initdb','psql','redis-server','redis-cli']:_binary(name)
        installed=True
    except RuntimeError:installed=False
    try:matched=installed and services_versions()=={'postgres':'17.11','redis':'8.0.2'}
    except RuntimeError:matched=False
    return {'installed':installed,'pinned_versions_match':matched,'pinned_postgres':'17.11','pinned_redis':'8.0.2','password_configured':bool(os.environ.get('DEV_SERVICES_PASSWORD')),'default_postgres_port':_ports()[0],'default_redis_port':_ports()[1]}


@command('services_versions',description='Inspect actual PostgreSQL and Redis pins without starting services or creating data.')
def services_versions() -> dict:
    with tempfile.TemporaryDirectory(prefix='abx-services-version-') as private:
        pg=_run([_binary('postgres'),'--version'],private)
        redis=_run([_binary('redis-server'),'--version'],private)
    postgres=re.search(r'PostgreSQL\) (\d+\.\d+)',pg);keyvalue=re.search(r'\bv=(\d+\.\d+\.\d+)',redis)
    if not postgres or not keyvalue:raise RuntimeError('actual service versions were not reported')
    return {'postgres':postgres[1],'redis':keyvalue[1]}


def _spawn(life,argv,port):
    private=tempfile.TemporaryDirectory(prefix='abx-dev-service-');root=Path(private.name);root.chmod(0o700)
    env=_environment(root);owner=secrets.token_hex(16);env['ABX_DEV_SERVICES_OWNER']=owner
    try:process=subprocess.Popen(argv,cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
    except BaseException:private.cleanup();raise
    def drain():
        try:
            while process.stdout.read(65536):pass
        finally:process.stdout.close()
    reader=threading.Thread(target=drain,daemon=True)
    life._STATE.update(process=process,private=private,reader=reader,port=port,owner=owner,pidfds={});reader.start()


def _sql(sql,password,private):
    env=_environment(private);env['PGPASSWORD']=password;env['PGCONNECT_TIMEOUT']='3'
    return _run([_binary('psql'),'-X','-A','-t','--no-password','--host','127.0.0.1','--port',str(_SESSION.get('postgres_port',5432)),'--username','sandbox','--dbname','postgres','--set','ON_ERROR_STOP=1','--command',sql],private,env=env)


def _redis(args,password,private):
    env=_environment(private);env['REDISCLI_AUTH']=password
    return _run([_binary('redis-cli'),'-e','--raw','-h','127.0.0.1','-p',str(_SESSION.get('redis_port',6379)),*args],private,env=env)


def _stop():
    errors=[]
    for life in [_REDIS,_PG]:
        try:life._stop()
        except Exception as exc:errors.append(type(exc).__name__)
    if errors:raise RuntimeError('owned service cleanup remains unconfirmed')
    private=_SESSION.get('private')
    if private:private.cleanup()
    _SESSION.clear()


@command('services_start',description='Start owned PostgreSQL/Redis with mandatory credentials, private config and explicit readiness. Existing caller data is preserved.')
def services_start(password: str='',data_dir: str='service-data',expose: bool=False,timeout_s: int=60,postgres_port: int=0,redis_port: int=0) -> dict:
    password=password or os.environ.get('DEV_SERVICES_PASSWORD','')
    if not re.fullmatch(r'[A-Za-z0-9_-]{16,128}',password):raise ValueError('password must be16..128 URL-safe ASCII characters')
    if not isinstance(expose,bool) or not 1<=timeout_s<=120:raise ValueError('expose must be boolean and timeout_s1..120')
    postgres_port,redis_port=_ports(postgres_port,redis_port)
    data=_data(data_dir)
    if not hasattr(os,'pidfd_open'):raise RuntimeError('Linux pidfd ownership is required')
    if os.geteuid()==0:raise RuntimeError('database services require the non-root image user')
    with _LOCK:
        if _SESSION or _PG._STATE or _REDIS._STATE:raise RuntimeError('stop existing owned services first')
        if services_versions()!={'postgres':'17.11','redis':'8.0.2'}:raise RuntimeError('installed database versions differ from reviewed pins')
        for port in [postgres_port,redis_port]:
            with socket.socket() as listener:
                listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
                try:listener.bind(('0.0.0.0',port))
                except OSError:raise RuntimeError('database port is already in use') from None
        fresh=not data.exists()
        if fresh:data.mkdir(mode=0o700)
        else:
            marker=data/'.abx-dev-services.json'
            if not marker.is_file() or json.loads(marker.read_text())!={'template':'dev-services','version':'1.0.0'}:
                raise ValueError('existing data_dir is not an initialized owned service directory')
            if any((data/name).is_symlink() for name in ['postgres','redis']):raise ValueError('service data must not be symlinked')
        private=tempfile.TemporaryDirectory(prefix='abx-services-config-');root=Path(private.name);root.chmod(0o700)
        _SESSION.update(private=private,password=password,data=data,postgres_port=postgres_port,redis_port=redis_port)
        try:
            postgres=data/'postgres';redis=data/'redis'
            if fresh:
                redis.mkdir(mode=0o700)
                pw=root/'init-password';pw.write_text(password+'\n');pw.chmod(0o600)
                _run([_binary('initdb'),'--pgdata',str(postgres),'--username','sandbox','--auth','scram-sha-256','--encoding','UTF8','--locale','C','--pwfile',str(pw),'--no-instructions'],root,timeout=timeout_s)
                pw.unlink()
                marker=data/'.abx-dev-services.json';marker.write_text(json.dumps({'template':'dev-services','version':'1.0.0'}));marker.chmod(0o600)
            host='0.0.0.0' if expose else '127.0.0.1'
            if expose:
                # This owned cluster is never a generic existing caller cluster.
                hba=postgres/'pg_hba.conf';text=hba.read_text()
                if '# abx explicit expose' not in text:hba.write_text(text+'\n# abx explicit expose\nhost all all 0.0.0.0/0 scram-sha-256\n')
            config=root/'redis.conf'
            config.write_text('bind '+host+'\nport '+str(redis_port)+'\nprotected-mode yes\nrequirepass '+password+'\ndir '+json.dumps(str(redis))+'\nappendonly yes\nappendfsync everysec\nmaxmemory 128mb\nmaxmemory-policy noeviction\nsave 60 1\n')
            config.chmod(0o600)
            _spawn(_PG,[_binary('postgres'),'-D',str(postgres),'-h',host,'-p',str(postgres_port),'-k',str(root),'-c','shared_buffers=64MB','-c','max_connections=20'],postgres_port)
            _spawn(_REDIS,[_binary('redis-server'),str(config)],redis_port)
            deadline=time.monotonic()+timeout_s
            while time.monotonic()<deadline:
                if not all(life._alive(life._STATE['process']) for life in [_PG,_REDIS]):raise RuntimeError('owned service exited before readiness')
                try:
                    if _sql('SELECT 1',password,root)=='1' and _redis(['PING'],password,root)=='PONG':return {'postgres':postgres_port,'redis':redis_port,'running':True,'exposed':expose}
                except RuntimeError:pass
                time.sleep(.1)
            raise RuntimeError('database readiness deadline exceeded')
        except BaseException:
            _stop()
            # Incomplete fresh initialization is owned by this run; never erase existing data.
            if fresh and not (data/'.abx-dev-services.json').exists():shutil.rmtree(data)
            raise


@command('services_status',description='Report owned service process liveness without returning credentials or data paths.')
def services_status() -> dict:
    with _LOCK:
        if not _SESSION:return {'running':False}
        return {'running':all(life._STATE and life._alive(life._STATE['process']) for life in [_PG,_REDIS]),'postgres':_SESSION['postgres_port'],'redis':_SESSION['redis_port']}


@command('services_sql',description='Execute bounded PostgreSQL SQL through literal psql argv; returns unaligned tuples, not raw diagnostics.')
def services_sql(sql: str) -> str:
    if not sql.strip() or len(sql.encode())>16384:raise ValueError('sql must be1..16384 bytes')
    with _LOCK:
        if not _SESSION:raise RuntimeError('owned services are not running')
        return _sql(sql,_SESSION['password'],Path(_SESSION['private'].name))


@command('services_redis',description='Run bounded PING/SET/GET/DEL/INCR through the owned Redis; no administrative commands.')
def services_redis(action: str='PING',key: str='',value: str='') -> str:
    if action not in ['PING','SET','GET','DEL','INCR']:raise ValueError('unsupported Redis action')
    if action!='PING' and (not key or len(key.encode())>1024):raise ValueError('key must be1..1024 bytes')
    if len(value.encode())>65536:raise ValueError('value exceeds64KiB')
    args=[action]+([key] if action!='PING' else [])+([value] if action=='SET' else [])
    with _LOCK:
        if not _SESSION:raise RuntimeError('owned services are not running')
        return _redis(args,_SESSION['password'],Path(_SESSION['private'].name))


@command('services_stop',description='Stop only owned service workers and verify process/listener absence. Database data remains for explicit reuse/removal.')
def services_stop() -> dict:
    with _LOCK:_stop();return {'running':False}


@command('services_self_test',description='Exercise actual SQL and Redis read/write, stop/restart persistence and nonce-owned data cleanup.')
def services_self_test() -> str:
    with _LOCK:
        if _SESSION:raise RuntimeError('stop existing services before self-test')
        name='abx_e2e_services_'+secrets.token_hex(6);password=secrets.token_urlsafe(24);created=False
        try:
            services_start(password,name);created=True
            if services_sql('SELECT 19+23')!='42':raise RuntimeError('actual SQL result mismatch')
            nonce=secrets.token_hex(12)
            services_sql('CREATE TABLE abx_proof (v text); INSERT INTO abx_proof VALUES (\''+nonce+'\')')
            if services_redis('SET','abx-proof',nonce)!='OK' or services_redis('GET','abx-proof')!=nonce:raise RuntimeError('actual Redis readback mismatch')
            services_stop();services_start(password,name)
            if services_sql('SELECT v FROM abx_proof')!=nonce or services_redis('GET','abx-proof')!=nonce:raise RuntimeError('persistent database readback mismatch')
        finally:
            if _SESSION.get('data')==_data(name):services_stop()
            if created:
                target=_data(name);shutil.rmtree(target)
                if target.exists():raise RuntimeError('owned database data cleanup remains unconfirmed')
    return 'POSTGRES_REDIS_OK'


def _exit():
    with _LOCK:_stop()
atexit.register(_exit)
if __name__=='__main__':start(int(os.environ.get('ABX_SERVER_PORT','9000')))
