"""Bound the original native NDJSON stream while retaining original settled events.

No model/provider implementation lives here. Original native records are emitted
unchanged; partial update duplicates are discarded. Native exit status is retained.
"""
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import threading

RETAIN={'agent_start','turn_start','message_end','turn_end','tool_execution_start','tool_execution_end','agent_end','error','compaction_end'}
RAW_LIMIT=16*1024*1024
LINE_LIMIT=1024*1024
RETAIN_LIMIT=256*1024


def filtered(source,output):
    total=0
    retained=0
    while True:
        line=source.readline(LINE_LIMIT+1)
        if not line:
            break
        total+=len(line)
        if len(line)>LINE_LIMIT or total>RAW_LIMIT:
            raise RuntimeError('original native JSON stream exceeds bound')
        value=json.loads(line)
        if not isinstance(value,dict):
            raise RuntimeError('original native JSON event must be an object')
        if value.get('type') not in RETAIN:
            continue
        retained+=len(line)
        if retained>RETAIN_LIMIT:
            raise RuntimeError('settled native event output exceeds256KiB')
        output.write(line)
        output.flush()


def main():
    binary='/opt/prime-agent/prime-agent'
    process=subprocess.Popen([binary,*sys.argv[1:]],stdin=sys.stdin.buffer,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    errors=[]
    exceeded=threading.Event()
    def drain():
        size=0
        while block:=process.stderr.read(65536):
            size+=len(block)
            if size>256*1024:
                exceeded.set()
                process.terminate()
            else:
                errors.append(block)
    thread=threading.Thread(target=drain,daemon=True)
    thread.start()
    try:
        filtered(process.stdout,sys.stdout.buffer)
        code=process.wait()
        thread.join(timeout=2)
        if thread.is_alive() or exceeded.is_set():
            raise RuntimeError('native stderr exceeds bound or did not settle')
        sys.stderr.buffer.write(b''.join(errors))
        sys.stderr.buffer.flush()
        if code<0:
            number=-code
            if number not in [signal.SIGKILL,signal.SIGSTOP]:signal.signal(number,signal.SIG_DFL)
            os.kill(os.getpid(),number)
        return code
    except BaseException:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        raise
    finally:
        process.stdout.close()
        process.stderr.close()


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print('Native event filtering failed ('+type(exc).__name__+'); raw content omitted',file=sys.stderr)
        raise SystemExit(1)
