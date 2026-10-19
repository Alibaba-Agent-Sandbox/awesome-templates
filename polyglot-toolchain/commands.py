"""Pinned Go, Rust and Java compilers; no model credentials or remote inference."""
from __future__ import annotations
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time
from agent_sandbox.server import command, start


def _run(argv: list[str], cwd: Path | None = None) -> str:
    env = os.environ.copy()
    if cwd is not None:
        env.update(GOCACHE=str(cwd / "go-cache"), GOPATH=str(cwd / "go-path"), GOTOOLCHAIN="local")
    proc = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    deadline = time.monotonic() + 90
    try:
        while os.waitid(os.P_PID, proc.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is None:
            if time.monotonic() >= deadline:
                raise TimeoutError("toolchain command exceeded90 seconds")
            time.sleep(0.02)
        # Hold the original leader until its process group has been stopped.
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        stdout, stderr = proc.communicate(timeout=5)
        if proc.returncode:
            raise RuntimeError("toolchain command failed: " + argv[0])
        return (stdout + stderr).decode(errors="replace").strip()
    finally:
        if proc.returncode is None:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.communicate(timeout=5)


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
