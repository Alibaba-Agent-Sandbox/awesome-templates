"""Authenticated, isolated code-server lifecycle with actual login verification."""
from __future__ import annotations
import atexit
import http.client
import json
import os
from pathlib import Path
import secrets
import select
import re
import shutil
import signal
import socket
import subprocess
import tempfile
import threading
import time
from urllib.parse import urlencode,urljoin,urlparse
from agent_sandbox.server import command,start

_LOCK=threading.RLock()
_STATE={}


def _run_process(argv: list[str], *, cwd: str, timeout: int | float,
                 env: dict | None = None, input_file=None) -> tuple[int, str, str]:
    """Keep the Linux session leader unreaped until its owned group is stopped."""
    process = subprocess.Popen(argv, cwd=cwd, env=env,
        stdin=input_file if input_file is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    stdout_parts: list[bytes] = []
    stderr_parts: list[bytes] = []
    overflow = threading.Event()
    def drain(stream, parts):
        size = 0
        try:
            while chunk := stream.read(65536):
                size += len(chunk)
                if size > 256 * 1024:
                    overflow.set()
                else:
                    parts.append(chunk)
        except OSError:
            pass
        finally:
            stream.close()
    readers = [threading.Thread(target=drain, args=(process.stdout, stdout_parts), daemon=True),
               threading.Thread(target=drain, args=(process.stderr, stderr_parts), daemon=True)]
    for reader in readers:
        reader.start()
    deadline = time.monotonic() + timeout
    timed_out = False
    try:
        while os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is None:
            if overflow.is_set():
                break
            if time.monotonic() >= deadline:
                timed_out = True
                break
            time.sleep(0.02)
    finally:
        # WNOWAIT pins the original PID/PGID even after leader exit. No poll(),
        # wait() or communicate() may reap it before group cleanup.
        if timed_out:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            grace = time.monotonic() + 1
            while time.monotonic() < grace:
                if os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None:
                    break
                time.sleep(0.02)
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            raise RuntimeError("owned process cleanup timed out") from None
        for reader in readers:
            reader.join(timeout=2)
    if overflow.is_set():
        raise RuntimeError("command output exceeded the 256 KiB per-stream limit") from None
    if timed_out:
        raise RuntimeError(f"command timed out after {timeout} seconds") from None
    return (process.returncode, b"".join(stdout_parts).decode("utf-8", "replace"),
            b"".join(stderr_parts).decode("utf-8", "replace"))



def _executable():
    executable=shutil.which("code-server")
    if not executable:
        raise RuntimeError("pinned code-server executable is unavailable")
    return executable


def _cwd(cwd=""):
    base=Path(os.environ.get("WORKSPACE","/home/user/app")).resolve(strict=True)
    path=Path(cwd) if cwd else base
    if not path.is_absolute():path=base/path
    path=path.resolve(strict=True)
    if not path.is_dir() or not path.is_relative_to(base):
        raise ValueError("cwd must be an existing WORKSPACE directory")
    return path


def _alive(process):
    return os.waitid(os.P_PID,process.pid,os.WEXITED|os.WNOHANG|os.WNOWAIT) is None


def _capture_owned():
    marker=("ABX_CODE_SERVER_OWNER="+_STATE["owner"]).encode()
    fds=_STATE.setdefault("pidfds",{})
    for entry in Path("/proc").iterdir():
        if not entry.name.isdecimal() or int(entry.name) in fds:continue
        fd=None
        try:
            if entry.stat().st_uid!=os.getuid() or marker not in (entry/"environ").read_bytes().split(b"\0"):continue
            fd=os.pidfd_open(int(entry.name))
            # Recheck after opening: never signal a reused/unrelated PID.
            if marker not in (entry/"environ").read_bytes().split(b"\0"):
                os.close(fd);continue
            fds[int(entry.name)]=fd
        except (FileNotFoundError,ProcessLookupError,PermissionError):
            if fd is not None:os.close(fd)


def _signal_owned(sig):
    _capture_owned()
    for fd in _STATE["pidfds"].values():
        try:signal.pidfd_send_signal(fd,sig)
        except ProcessLookupError:pass


def _listener_exists(port):
    paths=[Path("/proc/net/tcp")]
    if Path("/proc/net/tcp6").exists():paths.append(Path("/proc/net/tcp6"))
    for path in paths:
        for line in path.read_text().splitlines()[1:]:
            fields=line.split()
            if len(fields)>=4 and fields[3]=="0A" and int(fields[1].rsplit(":",1)[1],16)==port:
                return True
    return False


def _stop():
    process=_STATE.get("process")
    if process is None:return
    if not _STATE.get("group_stopped"):
        _signal_owned(signal.SIGTERM)
        try:os.killpg(process.pid,signal.SIGTERM)
        except ProcessLookupError:pass
        deadline=time.monotonic()+2
        while _alive(process) and time.monotonic()<deadline:time.sleep(.02)
        # The unique inherited owner marker covers detached upstream workers.
        # pidfds pin their identity; no unrelated process/group is authorized.
        _signal_owned(signal.SIGKILL)
        try:os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        _STATE["group_stopped"]=True
    process.wait(timeout=5)
    _STATE["reader"].join(timeout=2)
    deadline=time.monotonic()+3
    while True:
        _signal_owned(signal.SIGKILL)
        poller=select.poll()
        for fd in _STATE["pidfds"].values():poller.register(fd,select.POLLIN)
        live=len(poller.poll(0))<len(_STATE["pidfds"])
        closed=not _listener_exists(_STATE["port"])
        if closed and not live:break
        if time.monotonic()>=deadline:
            raise RuntimeError("owned IDE process/listener cleanup remains unconfirmed")
        time.sleep(.02)
    _STATE["private"].cleanup()
    for fd in _STATE.get("pidfds",{}).values():os.close(fd)
    _STATE.clear()


def _request(port,method,path,body="",cookie="",timeout=5):
    connection=http.client.HTTPConnection("127.0.0.1",port,timeout=timeout)
    headers={"Content-Type":"application/x-www-form-urlencoded"}
    if cookie:headers["Cookie"]=cookie
    try:
        connection.request(method,path,body,headers)
        response=connection.getresponse()
        content=response.read(2*1024*1024+1)
        if len(content)>2*1024*1024:raise RuntimeError("local UI response exceeds2MiB")
        return response.status,dict(response.getheaders()),content
    finally:connection.close()


@command("code_server_version",description="Inspect actual pinned code-server version with isolated configuration paths.")
def code_server_version() -> str:
    with tempfile.TemporaryDirectory(prefix="code-server-version-") as temporary:
        root=Path(temporary)
        code,stdout,_=_run_process([_executable(),"--version","--user-data-dir",str(root/"state"),"--extensions-dir",str(root/"extensions"),"--config",str(root/"config.yaml")],cwd=str(root),timeout=20,env={"PATH":os.environ.get("PATH","/usr/bin:/bin"),"LANG":"C.UTF-8","XDG_CONFIG_HOME":str(root/"config"),"XDG_DATA_HOME":str(root/"data")})
        if code:raise RuntimeError("code-server version inspection failed")
        match=re.search(r"^(\d+\.\d+\.\d+)\b",stdout,re.M)
        if not match:raise RuntimeError("actual code-server version was not reported")
        return match[1]


@command("code_server_start",description="Start the pinned browser IDE with mandatory password authentication and private config/state.")
def code_server_start(password: str="",port: int=8443,cwd: str="",timeout_s: int=60) -> dict:
    password=password or os.environ.get("CODE_SERVER_PASSWORD","")
    if not 12<=len(password.encode())<=256 or "\x00" in password:
        raise ValueError("a12..256-byte password is required")
    if not 1024<=port<=65535 or port==int(os.environ.get("ABX_SERVER_PORT","9000")):
        raise ValueError("port must be unreserved1024..65535")
    if not 1<=timeout_s<=120:raise ValueError("timeout_s must be1..120")
    directory=_cwd(cwd)
    if not hasattr(os,"pidfd_open") or not hasattr(signal,"pidfd_send_signal"):
        raise RuntimeError("Linux pidfd process ownership is required")
    with _LOCK:
        if _STATE.get("process") is not None:
            if not _STATE.get("group_stopped") and _alive(_STATE["process"]):raise RuntimeError("owned code-server is already running")
            _stop()
        with socket.socket() as listener:
            listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            try:listener.bind(("0.0.0.0",port))
            except OSError:raise RuntimeError("requested port is already in use") from None
        private=tempfile.TemporaryDirectory(prefix="abx-code-server-")
        root=Path(private.name)
        root.chmod(0o700)
        config=root/"config.yaml"
        config.write_text(json.dumps({"bind-addr":"0.0.0.0:"+str(port),"auth":"password","password":password,"cert":False}))
        config.chmod(0o600)
        owner=secrets.token_hex(16)
        env={"ABX_CODE_SERVER_OWNER":owner,"PATH":os.environ.get("PATH","/usr/local/bin:/usr/bin:/bin"),"LANG":"C.UTF-8","SHELL":"/bin/bash","XDG_CONFIG_HOME":str(root/"config"),"XDG_DATA_HOME":str(root/"data")}
        try:
            process=subprocess.Popen([_executable(),"--config",str(config),"--user-data-dir",str(root/"state"),"--extensions-dir",str(root/"extensions"),"--disable-telemetry","--disable-update-check",str(directory)],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True)
        except BaseException:
            private.cleanup()
            raise
        retained=bytearray()
        def drain():
            try:
                while block:=process.stdout.read1(8192):
                    if len(retained)+len(block)<=512*1024:retained.extend(block)
            finally:process.stdout.close()
        reader=threading.Thread(target=drain,daemon=True)
        _STATE.update(process=process,private=private,reader=reader,port=port,owner=owner,pidfds={})
        reader.start()
        try:
            deadline=time.monotonic()+timeout_s
            while time.monotonic()<deadline:
                if not _alive(process):raise RuntimeError("code-server exited before readiness; details omitted")
                try:
                    status,_,_= _request(port,"GET","/healthz",timeout=max(.01,min(1,deadline-time.monotonic())))
                    if status==200 and _alive(process):return {"port":port,"running":True,"auth":"password"}
                except (OSError,http.client.HTTPException):pass
                time.sleep(.1)
            raise RuntimeError("owned code-server readiness deadline exceeded")
        except BaseException:
            _stop()
            raise


@command("code_server_status",description="Report the owned IDE liveness without returning logs, cookies or passwords.")
def code_server_status() -> dict:
    with _LOCK:
        process=_STATE.get("process")
        if process is None:return {"running":False}
        if _STATE.get("group_stopped") or not _alive(process):
            _stop()
            return {"running":False}
        return {"running":True,"port":_STATE["port"],"auth":"password"}


@command("code_server_stop",description="Stop only the owned IDE group and remove its private config, state and logs.")
def code_server_stop() -> dict:
    with _LOCK:
        _stop()
        return {"running":False}


@command("code_server_self_test",description="Verify real password rejection, login cookie and authenticated workbench, then stop/clean the owned IDE.")
def code_server_self_test() -> str:
    password=secrets.token_urlsafe(24)
    with _LOCK:
        if _STATE.get("process") is not None:raise RuntimeError("stop the existing owned IDE before self-test")
        with socket.socket() as listener:
            listener.bind(("127.0.0.1",0));port=listener.getsockname()[1]
        code_server_start(password,port=port)
        private=Path(_STATE["private"].name)
        try:
            status,headers,_=_request(port,"GET","/")
            if status!=302 or "login" not in headers.get("Location",""):raise RuntimeError("unauthenticated UI was not rejected")
            _,headers,_=_request(port,"POST","/login",urlencode({"password":secrets.token_urlsafe(24)}))
            if headers.get("Set-Cookie"):raise RuntimeError("incorrect password received a session")
            status,headers,_=_request(port,"POST","/login",urlencode({"password":password}))
            if status!=302 or not headers.get("Set-Cookie"):raise RuntimeError("real login did not establish a session")
            cookie=headers["Set-Cookie"].split(";",1)[0]
            path="/"
            for _ in range(5):
                status,headers,content=_request(port,"GET",path,cookie=cookie)
                if status not in [301,302,303,307,308]:break
                location=urlparse(urljoin("http://127.0.0.1:"+str(port)+path,headers.get("Location","")))
                if location.hostname!="127.0.0.1" or location.port!=port:raise RuntimeError("unexpected UI redirect")
                path=location.path+("?"+location.query if location.query else "")
            if status!=200 or b"workbench" not in content:raise RuntimeError("authenticated workbench did not load")
        finally:code_server_stop()
        if private.exists():raise RuntimeError("owned IDE state cleanup failed")
        with socket.socket() as listener:
            listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            listener.bind(("0.0.0.0",port))
    return "CODE_SERVER_OK"


def _shutdown():
    with _LOCK:_stop()

atexit.register(_shutdown)
if __name__=="__main__":start(int(os.environ.get("ABX_SERVER_PORT","9000")))
