"""Bounded external controller processes and descendant cleanup.

Template startup/acceptance uses public_launch_e2e.py and the prepared-template
consumer. This module does not expose a second deployment/creation interface.
"""
from __future__ import annotations
import codecs
from dataclasses import dataclass
import os
import signal
import subprocess
import threading
import time
from typing import Any

@dataclass
class Proc:
    returncode: int
    stdout: str
    stderr: str


def _kill_process_group(pid: int) -> None:
    try:
        os.killpg(pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError, OSError):
        return
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.05)
    try:
        os.killpg(pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        pass


def _pump(pipe: Any, chunks: list[str], progress: dict[str, float]) -> None:
    decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
    try:
        while True:
            data = os.read(pipe.fileno(), 4096)
            if not data:
                final = decoder.decode(b'', final=True)
                if final:
                    chunks.append(final)
                break
            chunks.append(decoder.decode(data))
            progress['at'] = time.monotonic()
    finally:
        try:
            pipe.close()
        except OSError:
            pass


def run_monitored(
    argv: list[str],
    *,
    idle_timeout: float,
    wall_timeout: float,
    env: dict[str, str] | None = None,
) -> Proc:
    """Run ``argv`` in its own session. Kill the group when output goes idle.

    ``idle_timeout`` is a no-progress limit: any new stdout or stderr byte
    resets it. ``wall_timeout`` is a separate hard cap even while the
    process keeps printing. Cleanup is limited to its owned process group.
    """
    child_env = os.environ.copy() if env is None else dict(env)
    try:
        proc = subprocess.Popen(
            argv,
            env=child_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
    except OSError as exc:
        return Proc(127, "", f"failed to start {argv[0]}: {exc}")

    pgid = proc.pid
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    progress = {"at": time.monotonic()}
    started = progress["at"]
    threads = [
        threading.Thread(target=_pump, args=(proc.stdout, stdout_chunks, progress), daemon=True),
        threading.Thread(target=_pump, args=(proc.stderr, stderr_chunks, progress), daemon=True),
    ]
    for thread in threads:
        thread.start()
    reason = ""
    try:
        while True:
            # Keep the original leader unreaped until its process group is
            # stopped; poll()/wait() here would release the PID/PGID identity.
            exited = os.waitid(os.P_PID, proc.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
            now = time.monotonic()
            if exited is not None:
                break
            if now - progress["at"] >= idle_timeout:
                reason = "idle"
                print(
                    f"no process output for {idle_timeout:.0f}s; stopping process group {pgid}",
                    flush=True,
                )
                _kill_process_group(pgid)
                break
            if now - started >= wall_timeout:
                reason = "wall"
                print(
                    f"process wall clock {wall_timeout:.0f}s exceeded; stopping process group {pgid}",
                    flush=True,
                )
                _kill_process_group(pgid)
                break
            time.sleep(0.1)
    finally:
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait(timeout=5)
        for thread in threads:
            thread.join(timeout=2)

    stdout = "".join(stdout_chunks)
    stderr = "".join(stderr_chunks)
    if reason == "idle":
        stderr += (
            f"\nno process output progress for {idle_timeout:.0f}s "
            f"(no new output). Stopped process group {pgid}.\n"
        )
        return Proc(124, stdout, stderr)
    if reason == "wall":
        stderr += (
            f"\nprocess wall clock {wall_timeout:.0f}s exceeded while the process was still running. "
            f"Stopped process group {pgid}.\n"
        )
        return Proc(124, stdout, stderr)
    return Proc(proc.returncode or 0, stdout, stderr)
