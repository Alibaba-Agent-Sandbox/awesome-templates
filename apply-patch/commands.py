"""The official Codex apply_patch dialect, invoked by native argv0 and file stdin."""
from __future__ import annotations
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from agent_sandbox.server import command, start


# Generated from scripts/process_runners/file.py; update with scripts/sync_process_runners.py.
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


def _workspace(cwd: str) -> Path:
    base = Path(os.environ.get("WORKSPACE", "/home/user/app")).resolve(strict=True)
    path = Path(cwd) if cwd else base
    if not path.is_absolute():
        path = base / path
    resolved = path.resolve(strict=True)
    if not resolved.is_dir() or not resolved.is_relative_to(base):
        raise ValueError("cwd must be an existing directory inside WORKSPACE")
    return resolved


def _validate_paths(patch_text: str, root: Path) -> None:
    if not patch_text.strip() or len(patch_text.encode()) > 256 * 1024 or "\x00" in patch_text:
        raise ValueError("patch_text must be nonempty UTF-8 text of at most256KiB without NUL")
    for line in patch_text.splitlines():
        for prefix in ("*** Add File: ", "*** Update File: ", "*** Delete File: ", "*** Move to: "):
            if not line.startswith(prefix):
                continue
            name = line[len(prefix):]
            path = Path(name)
            if not name or path.is_absolute() or ".." in path.parts or "\\" in name:
                raise ValueError("patch paths must stay relative to the selected workspace")
            target = root / path
            if not target.resolve().is_relative_to(root):
                raise ValueError("patch path escapes the selected workspace")
            while target != root:
                if target.is_symlink():
                    raise ValueError("symlinked patch paths are unsupported")
                target = target.parent


def _binary() -> str:
    executable = shutil.which("apply_patch")
    if not executable:
        raise RuntimeError("pinned Codex apply_patch executable is unavailable")
    return executable


@command("apply_patch", description="Apply the Codex patch dialect to relative workspace paths; nonzero upstream results remain nonzero.")
def apply_patch(patch_text: str, cwd: str = "") -> dict:
    root = _workspace(cwd)
    _validate_paths(patch_text, root)
    # No shell, patch argv or model/cloud credentials. Stdin is a private file.
    with tempfile.TemporaryFile() as source:
        source.write(patch_text.encode())
        source.seek(0)
        code, stdout, stderr = _run_process([_binary()], cwd=str(root), timeout=30,
            env={"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"), "LANG": "C.UTF-8"}, input_file=source)
    return {"stdout": stdout, "stderr": stderr, "exit_code": code}


@command("apply_patch_version", description="Read the actual bundled native Codex version; no inference or login.")
def apply_patch_version() -> str:
    code, stdout, _ = _run_process([str(Path(_binary()).resolve()), "--version"], cwd=str(_workspace("")), timeout=10,
        env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8"})
    if code:
        raise RuntimeError("native Codex version inspection failed")
    return stdout.strip()


@command("apply_patch_smoke", description="Verify actual add/update/move/delete bytes and literal shell text in an owned temporary project.")
def apply_patch_smoke() -> str:
    with tempfile.TemporaryDirectory(prefix="patch-proof-", dir=_workspace("")) as temporary:
        root = Path(temporary)
        (root / "before.txt").write_text("old\n")
        (root / "remove.txt").write_text("remove\n")
        patch = "*** Begin Patch\n*** Update File: before.txt\n*** Move to: after.txt\n@@\n-old\n+new\n*** Add File: added.txt\n+$(touch SHOULD_NOT_EXIST)\n*** Delete File: remove.txt\n*** End Patch\n"
        result = apply_patch(patch, cwd=str(root))
        if result["exit_code"] or (root / "after.txt").read_text() != "new\n" or (root / "added.txt").read_text() != "$(touch SHOULD_NOT_EXIST)\n" or (root / "before.txt").exists() or (root / "remove.txt").exists() or (root / "SHOULD_NOT_EXIST").exists():
            raise RuntimeError("actual Codex patch output mismatch")
    if root.exists():
        raise RuntimeError("owned patch project cleanup failed")
    return "APPLY_PATCH_OK"


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
