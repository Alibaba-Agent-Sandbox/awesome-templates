"""Install exact official archives, verify SHA256, retain upstream licenses."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile
import tempfile
import time
import urllib.error
import urllib.request


def install(prefix: Path) -> None:
    assets = json.loads(Path(__file__).with_name("toolchains.json").read_text())
    arch = platform.machine()
    mapping = {"x86_64": ("amd64", "x64"), "aarch64": ("arm64", "aarch64")}
    if arch not in mapping:
        raise RuntimeError("only Linux x86_64 and aarch64 are supported")
    go_arch, java_arch = mapping[arch]
    prefix.mkdir(parents=True, exist_ok=True)
    def fetch(asset, directory):
        archive = directory / "archive"
        for attempt in range(4):
            try:
                digest = hashlib.sha256()
                size = 0
                with urllib.request.urlopen(asset["url"], timeout=90) as response, archive.open("wb") as out:
                    while block := response.read(1024 * 1024):
                        size += len(block)
                        if size > 300 * 1024 * 1024:
                            raise RuntimeError("toolchain archive exceeds size budget")
                        digest.update(block)
                        out.write(block)
                if digest.hexdigest() != asset["sha256"]:
                    raise RuntimeError("toolchain archive SHA256 mismatch")
                with tarfile.open(archive) as source:
                    source.extractall(directory / "unpacked", filter="data")
                archive.unlink()
                return directory / "unpacked"
            except (urllib.error.URLError, TimeoutError):
                archive.unlink(missing_ok=True)
                if attempt == 3:
                    raise RuntimeError("pinned toolchain download failed") from None
                time.sleep(2 ** attempt)
    with tempfile.TemporaryDirectory(prefix="toolchain-install-") as temporary:
        temp = Path(temporary)
        for name, asset in [("go", assets["go"]["assets"][go_arch]), ("java", assets["java"]["assets"][java_arch])]:
            directory = temp / name
            directory.mkdir()
            unpacked = fetch(asset, directory)
            roots = list(unpacked.iterdir())
            if len(roots) != 1 or not roots[0].is_dir():
                raise RuntimeError("unexpected toolchain archive layout")
            shutil.move(str(roots[0]), str(prefix / name))
            shutil.rmtree(directory)
        for name, asset in assets["rust_components"][arch].items():
            directory = temp / name
            directory.mkdir()
            unpacked = fetch(asset, directory)
            roots = list(unpacked.iterdir())
            if len(roots) != 1 or not (roots[0] / "install.sh").is_file():
                raise RuntimeError("unexpected Rust component layout")
            subprocess.run(["sh", str(roots[0] / "install.sh"), "--prefix=" + str(prefix / "rust"), "--disable-ldconfig"], check=True, timeout=180)
            shutil.rmtree(directory)
    # This is the actual rootfs, not a compressed archive size estimate.
    used = shutil.disk_usage(prefix).used
    print(json.dumps({"installed_rootfs_used_bytes": used, "budget_bytes": 8 * 1024**3}))
    if used > 8 * 1024**3:
        raise RuntimeError("toolchains exceed the reviewed 8 GiB used-rootfs budget")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", type=Path, default=Path("/opt/toolchains"))
    install(parser.parse_args().prefix)
