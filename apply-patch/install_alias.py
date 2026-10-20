"""Validate the official locked Codex native binary and install its argv0 alias."""
import argparse
import json
from pathlib import Path
import platform
import subprocess


def install(node_modules: Path, bin_dir: Path) -> None:
    root=node_modules/'@openai'
    if json.loads((root/'codex/package.json').read_text())['version']!='0.162.1':
        raise RuntimeError('expected official Codex0.162.1')
    arch={'x86_64':'x64','aarch64':'arm64'}[platform.machine()]
    package=root/('codex-linux-'+arch)
    if json.loads((package/'package.json').read_text())['version']!='0.162.1-linux-'+arch:
        raise RuntimeError('native Codex package version mismatch')
    binaries=list(package.glob('vendor/*/bin/codex'))
    if len(binaries)!=1:
        raise RuntimeError('one official pinned native Codex binary is required')
    binary=binaries[0].resolve()
    version=subprocess.run([str(binary),'--version'],capture_output=True,text=True,timeout=10,check=True)
    if version.stdout.strip()!='codex-cli 0.162.1':
        raise RuntimeError('actual native Codex version mismatch')
    bin_dir.mkdir(parents=True,exist_ok=True)
    (bin_dir/'apply_patch').symlink_to(binary)
    print('PASS actual codex-cli0.162.1; native apply_patch alias installed')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node-modules',type=Path,required=True)
    parser.add_argument('--bin',type=Path,required=True)
    args=parser.parse_args()
    install(args.node_modules,args.bin)
