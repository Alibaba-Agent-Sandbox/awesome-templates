"""Bounded per-call process using identity-pinned group/marked-worker cleanup."""
import importlib.util
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import threading
import time


def run(argv,*,cwd,timeout,env,input_file=None):
    spec=importlib.util.spec_from_file_location('owned_Cursor_process_'+secrets.token_hex(8),Path(__file__).with_name('lifecycle.py'))
    life=importlib.util.module_from_spec(spec);spec.loader.exec_module(life)
    private=tempfile.TemporaryDirectory(prefix='abx-devin-call-');root=Path(private.name);root.chmod(0o700)
    env=dict(env)
    owner=secrets.token_hex(16);env.update(ABX_DEVIN_OWNER=owner,PYTHONIOENCODING='utf-8')
    try:p=subprocess.Popen(argv,cwd=cwd,env=env,stdin=input_file or subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    except BaseException:private.cleanup();raise
    out=[];err=[];overflow=threading.Event()
    def drain(stream,parts):
        size=0
        try:
            while chunk:=stream.read(65536):
                size+=len(chunk)
                if size>256*1024:overflow.set()
                else:parts.append(chunk)
        finally:stream.close()
    readers=[threading.Thread(target=drain,args=(p.stdout,out),daemon=True),threading.Thread(target=drain,args=(p.stderr,err),daemon=True)]
    life._STATE.update(process=p,private=private,reader=readers[0],port=0,owner=owner,pidfds={})
    for thread in readers:thread.start()
    timed_out=False;deadline=time.monotonic()+timeout
    try:
        while life._alive(p):
            if overflow.is_set():break
            if time.monotonic()>=deadline:timed_out=True;break
            time.sleep(.02)
    finally:
        life._stop()
        for thread in readers:thread.join(timeout=2)
        if any(thread.is_alive() for thread in readers):raise RuntimeError('owned Cursor pipe cleanup not confirmed')
    if overflow.is_set():raise RuntimeError('Cursor output exceeded256KiB per stream; output omitted')
    if timed_out:raise RuntimeError('Cursor execution exceeded timeout_s; output omitted')
    return p.returncode,b''.join(out).decode('utf-8','replace'),b''.join(err).decode('utf-8','replace')
