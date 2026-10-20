"""Identity-safe Linux lifecycle for this standalone service template."""
import os
from pathlib import Path
import select
import signal
import threading
import time
_LOCK=threading.RLock()
_STATE={}


def _alive(process):
    return os.waitid(os.P_PID,process.pid,os.WEXITED|os.WNOHANG|os.WNOWAIT) is None


def _capture_owned():
    marker=("ABX_BROWSER_USE_OWNER="+_STATE["owner"]).encode()
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
            raise RuntimeError("owned BrowserUse process/listener cleanup remains unconfirmed")
        time.sleep(.02)
    _STATE["private"].cleanup()
    for fd in _STATE.get("pidfds",{}).values():os.close(fd)
    _STATE.clear()
