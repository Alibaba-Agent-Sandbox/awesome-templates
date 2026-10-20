"""Install one exact official CPU GNU asset, preserving its bytes and license."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tarfile
import tempfile
import time
import urllib.request


def install(prefix: Path, *, check_rootfs: bool = False):
    if prefix.exists() or prefix.is_symlink():
        raise FileExistsError("installation prefix must be new")
    if platform.system() != "Linux":
        raise RuntimeError("this reviewed profile supports Linux only")
    manifest = json.loads(Path(__file__).with_name("assets.json").read_text())
    item = manifest["assets"].get(platform.machine())
    if not item:
        raise RuntimeError("no reviewed official asset for this architecture")
    prefix.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="abx-goose-install-", dir=prefix.parent) as temporary:
        root = Path(temporary); archive = root / "goose.tar.bz2"; size = 0; digest = hashlib.sha256()
        deadline = time.monotonic() + 240
        with urllib.request.urlopen(item["url"], timeout=30) as response, archive.open("xb") as output:
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > item["bytes"] or time.monotonic() > deadline:
                    raise RuntimeError("official asset exceeded byte/deadline budget")
                output.write(chunk); digest.update(chunk)
        if size != item["bytes"] or digest.hexdigest() != item["sha256"]:
            raise RuntimeError("official Goose asset integrity mismatch")
        staged = root / "install"; staged.mkdir()
        with tarfile.open(archive) as source:
            members = [m for m in source.getmembers() if m.isfile() and Path(m.name).name == "goose"]
            if len(members) != 1 or not 0 < members[0].size <= 400 * 1024**2:
                raise RuntimeError("one bounded official Goose executable is required")
            with source.extractfile(members[0]) as data, (staged / "goose").open("xb") as output:
                shutil.copyfileobj(data, output, 1024 * 1024)
            for member in source.getmembers():
                path = Path(member.name)
                if not member.isfile() or not path.name.lower().startswith(("license", "notice", "copying", "copyright")):
                    continue
                if path.is_absolute() or ".." in path.parts or member.size > 4 * 1024**2:
                    raise RuntimeError("invalid bundled notice member")
                target = staged / "upstream-notices" / path
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.extractfile(member) as data, target.open("xb") as output:
                    shutil.copyfileobj(data, output, 1024 * 1024)
        (staged / "goose").chmod(0o755)
        shutil.copy2(Path(__file__).with_name("upstream-LICENSE"), staged / "LICENSE")
        home = root / "home"; home.mkdir(mode=0o700)
        result = subprocess.run([str(staged / "goose"), "--version"], capture_output=True, text=True, timeout=20,
            env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(home), "GOOSE_PATH_ROOT": str(home), "GOOSE_DISABLE_KEYRING": "1"})
        if result.returncode or result.stdout.strip() != manifest["version"]:
            raise RuntimeError("installed official Goose version mismatch")
        staged.rename(prefix)
    if check_rootfs:
        result = subprocess.run(["du", "-sx", "--block-size=1", "/"], capture_output=True, text=True, timeout=90)
        if result.returncode or int(result.stdout.split()[0]) > 8 * 1024**3:
            raise RuntimeError("visible image rootfs exceeds8GiB or size could not be verified")
    print("PASS official Goose" + manifest["version"] + "; fixed architecture asset/SHA256")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--prefix", type=Path, default=Path("/opt/goose"))
    parser.add_argument("--check-rootfs", action="store_true")
    args = parser.parse_args(); install(args.prefix, check_rootfs=args.check_rootfs)
