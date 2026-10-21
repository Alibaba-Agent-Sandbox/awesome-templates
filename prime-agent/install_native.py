"""Install the unchanged official native release and every original sidecar."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tarfile
import tempfile
import urllib.request


def install(metadata,root):
    if (metadata['version']!='0.10.0' or metadata['url']!='https://github.com/PrimeIntellect-ai/prime-agent/releases/download/v0.10.0/prime-agent-0.10.0-linux-x64.tar.gz'
            or metadata['sha256']!='c16bd2af5e77b53f49b914a44742c4cf6a67c5ed5000041430b78dbd4c3bcbec'):
        raise ValueError('unreviewed original Prime Agent release')
    root.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='abx-prime-install-') as value:
        private=Path(value)
        target=private/'native.tar.gz'
        size=0
        digest=hashlib.sha256()
        with urllib.request.urlopen(metadata['url'],timeout=120) as source,target.open('xb') as output:
            while block:=source.read(1024*1024):
                size+=len(block)
                if size>metadata['size']:
                    raise RuntimeError('native archive exceeds expected size')
                digest.update(block)
                output.write(block)
        if size!=21556959 or digest.hexdigest()!=metadata['sha256']:
            raise RuntimeError('original release archive size/SHA256 differs')
        with tarfile.open(target,'r:gz') as bundle:
            members=bundle.getmembers()
            if len(members)>512 or sum(item.size for item in members)>128*1024*1024:
                raise RuntimeError('native release expansion exceeds reviewed bounds')
            for item in members:
                path=PurePosixPath(item.name)
                if path.is_absolute() or '..' in path.parts or not (item.isfile() or item.isdir()):
                    raise RuntimeError('invalid original release member')
                output=root/str(path)
                if item.isdir():
                    output.mkdir(parents=True,exist_ok=True)
                    continue
                if item.size>96*1024*1024:
                    raise RuntimeError('native member exceeds96MiB')
                output.parent.mkdir(parents=True,exist_ok=True)
                with bundle.extractfile(item) as source,output.open('xb') as dest:
                    while block:=source.read(1024*1024):
                        dest.write(block)
                output.chmod(0o755 if item.mode&0o111 else 0o644)
        binary=root/'prime-agent'
        with binary.open('rb') as source:
            if binary.stat().st_size!=61057216 or hashlib.file_digest(source,'sha256').hexdigest()!=metadata['binary_sha256']:
                raise RuntimeError('actual original Prime Agent binary integrity differs')
        result=subprocess.run([str(binary),'--version'],cwd=private,
            env={'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':value,'LANG':'C.UTF-8'},
            capture_output=True,text=True,timeout=30,check=True)
        if result.stdout.strip()!='0.10.0':
            raise RuntimeError('actual original native Prime Agent version differs')
    print('Verified original Prime Agent0.10.0 archive, executable SHA256, full sidecars and native version')


if __name__=='__main__':
    install(json.loads(Path('/opt/prime-bootstrap/upstream.json').read_text()),Path('/opt/prime-agent'))
