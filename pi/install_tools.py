#!/usr/bin/env python3
"""Install fixed official fd/rg archives after GitHub-published SHA256 verification."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import platform
import subprocess
import tarfile
import tempfile
import urllib.request

SOURCES = {
    'fd': ('10.5.0', 'sharkdp/fd', 'v10.5.0', 'fd-v10.5.0-{arch}-unknown-linux-musl', {
        'x86_64': '761c72dc8e120d85b22292063be8a796e2eeb20eb3e4f38b8fa2343ccf3514a7',
        'aarch64': 'd76c4317f7d5dba69f8a2a15856c90c777e7f0dd4e85f0de8c76de6992c374d4'}),
    'rg': ('15.2.0', 'BurntSushi/ripgrep', '15.2.0', 'ripgrep-15.2.0-{arch}-unknown-linux-musl', {
        'x86_64': '33e15bcf1624b25cdd2a55813a47a2f95dbe126268203e76aa6a585d1e7b149c',
        'aarch64': '800b1e7206afe799dfb5a6901f23147cfaabe0e52210538100f61e86e1740915'}),
}


def install(root: Path, binary_directory: Path) -> None:
    architecture = platform.machine()
    if architecture not in {'x86_64', 'aarch64'}:
        raise RuntimeError('only official Linux x86_64/aarch64 artifacts are supported')
    root.mkdir(parents=True, exist_ok=True)
    binary_directory.mkdir(parents=True, exist_ok=True)
    for tool, (version, repository, tag, pattern, checksums) in SOURCES.items():
        name = pattern.format(arch=architecture)
        destination = root / name
        with tempfile.TemporaryDirectory(prefix='pi-tool-download-') as temporary:
            archive = Path(temporary) / (name + '.tar.gz')
            urllib.request.urlretrieve(f'https://github.com/{repository}/releases/download/{tag}/{name}.tar.gz',archive)
            with archive.open('rb') as stream:
                digest = hashlib.file_digest(stream,'sha256').hexdigest()
            if digest != checksums[architecture]:
                raise RuntimeError(tool + ' official archive SHA256 mismatch')
            with tarfile.open(archive) as source:
                source.extractall(root,filter='data')
        executable = destination / tool
        if not executable.is_file():
            raise RuntimeError(tool + ' archive has no expected executable')
        link = binary_directory / tool
        if link.is_symlink() or link.exists():
            link.unlink()
        link.symlink_to(executable.resolve())
        actual = subprocess.check_output([str(link),'--version'],text=True)
        if version not in actual.split():
            raise RuntimeError(tool + ' version mismatch')
        print('PASS official pinned ' + tool + ' ' + version + '; archive SHA256 verified')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('/opt/pi-tools'))
    parser.add_argument('--bin', type=Path, default=Path('/usr/local/bin'))
    args = parser.parse_args()
    install(args.root,args.bin)
