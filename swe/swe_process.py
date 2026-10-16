"""Linux owned process sessions with bounded output and cleanup before reaping."""
import os
import signal
import subprocess
import threading
import time


def run(argv, *, cwd, env, timeout, input_text=None):
    process = subprocess.Popen(argv, cwd=cwd, env=env, start_new_session=True,
        stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    chunks = [bytearray(), bytearray()]
    def drain(stream, result):
        try:
            while part := stream.read(65536):
                if len(result) < 2 * 1024 * 1024:
                    result.extend(part[:2 * 1024 * 1024 - len(result)])
        finally:
            stream.close()
    readers = [threading.Thread(target=drain, args=(stream, result), daemon=True)
               for stream, result in zip((process.stdout, process.stderr), chunks)]
    for reader in readers:
        reader.start()
    feeder = None
    if input_text is not None:
        def feed():
            try:
                process.stdin.write(input_text.encode()); process.stdin.close()
            except (BrokenPipeError, OSError):
                process.stdin.close()
        feeder = threading.Thread(target=feed, daemon=True); feeder.start()
    deadline = time.monotonic() + timeout
    timed_out = False
    try:
        while os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is None:
            if time.monotonic() >= deadline:
                timed_out = True; break
            time.sleep(.02)
    finally:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=5)
        for reader in readers:
            reader.join(timeout=3)
        if feeder:
            feeder.join(timeout=3)
        if any(reader.is_alive() for reader in readers) or (feeder and feeder.is_alive()):
            raise RuntimeError('owned process IO cleanup timed out')
    if timed_out:
        raise RuntimeError('owned process deadline exceeded')
    return process.returncode, *(part.decode('utf-8', 'replace') for part in chunks)


def action(command, *, cwd, env, timeout):
    """Run one shell action inside the existing owned CLI process group.

    On timeout the exception must terminate the CLI; its owning caller then
    kills the entire shared group. This function creates no detached session.
    """
    process = subprocess.Popen(command, shell=True, executable='/bin/bash', cwd=cwd,
        env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    chunks = bytearray()
    def drain():
        try:
            while chunk := process.stdout.read(65536):
                if len(chunks) < 2 * 1024 * 1024:
                    chunks.extend(chunk[:2 * 1024 * 1024 - len(chunks)])
        finally:
            process.stdout.close()
    reader = threading.Thread(target=drain, daemon=True);reader.start()
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
        raise RuntimeError('model action deadline exceeded') from None
    reader.join(timeout=.5)
    return {'output': bytes(chunks).decode('utf-8', 'replace')[-20000:],
            'returncode': process.returncode, 'exception_info': ''}
