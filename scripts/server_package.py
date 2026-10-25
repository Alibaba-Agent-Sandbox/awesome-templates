"""Read a template's exact public server package dependency."""
from __future__ import annotations

from pathlib import Path
import re
import sys

_PIN = re.compile(r'agent-sandbox-server==([0-9]+\.[0-9]+\.[0-9]+(?:[A-Za-z0-9.+-]*)?)')


def server_version(source: Path, dockerfile: str = 'Dockerfile') -> str:
    path = source / dockerfile
    if not path.resolve().is_relative_to(source.resolve()):
        raise ValueError('server package Dockerfile must stay inside the template')
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 256 * 1024:
        raise ValueError('server package requires a regular bounded Dockerfile')
    text = '\n'.join(line for line in path.read_text().splitlines()
                     if not line.lstrip().startswith('#'))
    pins = set(_PIN.findall(text))
    if len(pins) != 1:
        raise ValueError('Dockerfile requires one exact public agent-sandbox-server package version')
    return pins.pop()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: server_package.py TEMPLATE_DIRECTORY')
    print(server_version(Path(sys.argv[1])))
