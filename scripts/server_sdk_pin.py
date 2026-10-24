"""Resolve a template opt-in to an immutable public server SDK source.

Stdlib only so keyless CI can resolve its checkout before installing packages.
Contexts without an override use the common pin. Every declared Dockerfile
fallback must agree with the injected source used by CI.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

SERVER_COMMIT = 'e2cb27e24fde0a67112f82b8d44af463445a5d1a'
_ARCHIVE = re.compile(r'https://github\.com/(?i:alibaba-agent-sandbox/python-sdk)/archive/([^\s"\x27]+)')
_PIN = re.compile(r'([0-9a-f]{40})\.tar\.gz#subdirectory=server-sdk')


def server_commit(source: Path) -> str:
    pin_file = source / 'server-sdk.commit'
    explicit = pin_file.exists() or pin_file.is_symlink()
    selected = SERVER_COMMIT
    if explicit:
        if pin_file.is_symlink() or not pin_file.is_file() or pin_file.stat().st_size != 41:
            raise ValueError('server-sdk.commit requires one immutable40-character commit and newline')
        value = pin_file.read_text()
        if not re.fullmatch(r'[0-9a-f]{40}\n', value):
            raise ValueError('server-sdk.commit requires one immutable40-character commit and newline')
        selected = value.strip()
    path = source / 'Dockerfile'
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 256 * 1024:
        raise ValueError('server source requires a regular bounded Dockerfile')
    archives = _ARCHIVE.findall(path.read_text())
    if not archives:
        if explicit:
            raise ValueError('explicit server SDK source requires its public Dockerfile fallback')
        return selected
    pins = []
    for archive in archives:
        match = _PIN.fullmatch(archive)
        if not match:
            raise ValueError('server SDK archive must use one exact public40-character commit')
        pins.append(match[1])
    if len(set(pins)) != 1:
        raise ValueError('Dockerfile declares conflicting server SDK commits')
    if pins[0] != selected:
        raise ValueError('selected CI server SDK source differs from the Dockerfile fallback')
    return selected


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: server_sdk_pin.py TEMPLATE_DIRECTORY')
    print(server_commit(Path(sys.argv[1])))
