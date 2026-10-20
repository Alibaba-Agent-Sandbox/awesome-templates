"""Pinned Go, Rust and Java compilers; no model credentials or remote inference."""
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


def _run(argv: list[str], cwd: Path | None = None) -> str:
    env = {name: os.environ[name] for name in ("PATH", "HOME", "JAVA_HOME", "TMPDIR") if name in os.environ}
    env.update(LANG="C.UTF-8", LC_ALL="C.UTF-8", GOTOOLCHAIN="local")
    if cwd is not None:
        env.update(GOCACHE=str(cwd / "go-cache"), GOPATH=str(cwd / "go-path"))
    proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    parts = [[], []]
    overflow = threading.Event()
    def drain(stream, output):
        size = 0
        try:
            while chunk := stream.read(65536):
                size += len(chunk)
                if size > 256 * 1024:
                    overflow.set()
                else:
                    output.append(chunk)
        finally:
            stream.close()
    readers = [threading.Thread(target=drain, args=(stream, output), daemon=True)
        for stream, output in zip((proc.stdout, proc.stderr), parts)]
    for reader in readers:
        reader.start()
    deadline = time.monotonic() + 90
    timed_out = False
    try:
        while os.waitid(os.P_PID, proc.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is None:
            if overflow.is_set():
                break
            if time.monotonic() >= deadline:
                timed_out = True
                break
            time.sleep(0.02)
    finally:
        # Keep the original leader unreaped until its owned process group is stopped.
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait(timeout=5)
        for reader in readers:
            reader.join(timeout=2)
        if any(reader.is_alive() for reader in readers):
            raise RuntimeError("owned toolchain output pipes did not close")
    if overflow.is_set():
        raise RuntimeError("toolchain command output exceeded256 KiB per stream")
    if timed_out:
        raise TimeoutError("toolchain command exceeded90 seconds")
    if proc.returncode:
        raise RuntimeError("toolchain command failed: " + argv[0])
    return b"".join(parts[0] + parts[1]).decode(errors="replace").strip()


@command("toolchain_versions", description="Inspect actual pinned Go, Rust and Temurin versions and disk usage.")
def toolchain_versions() -> dict:
    result = {}
    for name, argv in {"go": ["go", "version"], "rustc": ["rustc", "--version"], "cargo": ["cargo", "--version"], "java": ["java", "-version"], "javac": ["javac", "-version"]}.items():
        result[name] = _run(argv).splitlines()[0] if shutil.which(argv[0]) else None
    disk = shutil.disk_usage("/")
    result.update(rootfs_used_bytes=disk.used, rootfs_free_bytes=disk.free, non_root=os.geteuid() != 0)
    return result


@command("toolchain_smoke", description="Compile and execute owned Go, Rust and Java hello programs; remove their source and artifacts.")
def toolchain_smoke() -> dict:
    for name in ["go", "rustc", "java", "javac", "gcc"]:
        if not shutil.which(name):
            raise RuntimeError("required toolchain is unavailable: " + name)
    with tempfile.TemporaryDirectory(prefix="toolchain-smoke-") as temporary:
        root = Path(temporary)
        (root / "main.go").write_text('package main; import "fmt"; func main(){fmt.Println("GO_OK")}')
        (root / "main.rs").write_text('fn main(){println!("RUST_OK");}')
        (root / "Main.java").write_text('class Main {public static void main(String[] a){System.out.println("JAVA_OK");}}')
        _run(["go", "build", "-o", str(root / "go-proof"), str(root / "main.go")], root)
        _run(["rustc", str(root / "main.rs"), "-o", str(root / "rust-proof")], root)
        _run(["javac", str(root / "Main.java")], root)
        result = {"go": _run([str(root / "go-proof")]), "rust": _run([str(root / "rust-proof")]), "java": _run(["java", "-cp", str(root), "Main"])}
        if result != {"go": "GO_OK", "rust": "RUST_OK", "java": "JAVA_OK"}:
            raise RuntimeError("compiled toolchain output mismatch")
    result["cleanup_verified"] = not root.exists()
    return result


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
