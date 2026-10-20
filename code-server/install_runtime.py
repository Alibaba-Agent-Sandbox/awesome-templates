"""Install the pinned official standalone code-server archive and retain notices."""
import hashlib
import argparse
import subprocess
import json
from pathlib import Path
import platform
import shutil
import tarfile
import tempfile
import time
import urllib.error
import urllib.request


def install(prefix: Path, *, check_rootfs: bool=False) -> None:
    arch={"x86_64":"amd64","aarch64":"arm64"}[platform.machine()]
    metadata=json.loads(Path(__file__).with_name("assets.json").read_text())
    asset=next(a for a in metadata["assets"] if a["name"]=="code-server-4.141.0-linux-"+arch+".tar.gz")
    with tempfile.TemporaryDirectory(prefix="code-server-download-") as temporary:
        archive=Path(temporary)/"runtime.tar.gz"
        deadline=time.monotonic()+240
        for attempt in range(4):
            try:
                size=0
                digest=hashlib.sha256()
                with urllib.request.urlopen(asset["browser_download_url"],timeout=60) as response,archive.open("wb") as output:
                    while block:=response.read(1024*1024):
                        size+=len(block)
                        if size>asset["size"] or time.monotonic()>deadline:
                            raise RuntimeError("code-server archive exceeds download budget")
                        digest.update(block)
                        output.write(block)
                if size!=asset["size"] or "sha256:"+digest.hexdigest()!=asset["digest"]:
                    raise RuntimeError("official code-server archive integrity mismatch")
                break
            except (urllib.error.URLError,TimeoutError):
                if attempt==3 or time.monotonic()>deadline:
                    raise RuntimeError("pinned code-server download failed") from None
                time.sleep(2**attempt)
        prefix.mkdir(parents=True,exist_ok=True)
        with tarfile.open(archive) as source:
            source.extractall(prefix,filter="data")
        (prefix/"current").symlink_to(prefix/("code-server-4.141.0-linux-"+arch))
    installed=sum(p.stat().st_size for p in prefix.rglob("*") if p.is_file() and not p.is_symlink())
    report={"installed_file_bytes":installed,"version":"4.141.0"}
    if check_rootfs:
        # Container df reports the host backing filesystem. du counts this
        # image's visible root filesystem, excluding separate mounted filesystems.
        used=int(subprocess.check_output(["du","-sx","--block-size=1","/"],timeout=120).split()[0])
        report["visible_rootfs_used_bytes"]=used
        if used>8*1024**3:
            raise RuntimeError("installed code-server exceeds8GiB visible-rootfs budget")
    print(json.dumps(report))

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix",type=Path,default=Path("/opt/code-server"))
    parser.add_argument("--check-rootfs",action="store_true",help="Image build only: enforce actual visible rootfs budget")
    args=parser.parse_args()
    install(args.prefix,check_rootfs=args.check_rootfs)
