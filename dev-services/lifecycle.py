"""Identity-safe Linux lifecycle for this standalone service template."""
import http.client
import os
from pathlib import Path
import select
import signal
import subprocess
import threading
import time
_LOCK=threading.RLock()
_STATE={}


def _alive(process):
    return os.waitid(os.P_PID,process.pid,os.WEXITED|os.WNOHANG|os.WNOWAIT) is None


def _capture_owned():
    marker=("ABX_DEV_SERVICES_OWNER="+_STATE["owner"]).encode()
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
            raise RuntimeError("owned development server process/listener cleanup remains unconfirmed")
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
