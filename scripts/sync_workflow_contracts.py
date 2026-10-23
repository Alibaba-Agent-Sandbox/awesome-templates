#!/usr/bin/env python3
"""Synchronize exact, committed workflow contracts; validate offline with --check."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'spec/contracts'
FILES = ('workflow-v1.json', 'verification-profiles.json', 'receipt.schema.json')
LOCK = TARGET / 'source-lock.json'


def verify() -> None:
    lock = json.loads(LOCK.read_text())
    if lock['repository'] != 'https://github.com/Alibaba-Agent-Sandbox/python-sdk' or not re.fullmatch('[0-9a-f]{40}', lock['revision']):
        raise ValueError('invalid contract source identity')
    if set(lock['files']) != set(FILES):
        raise ValueError('incomplete contract manifest')
    for name in FILES:
        if hashlib.sha256((TARGET / name).read_bytes()).hexdigest() != lock['files'][name]:
            raise ValueError('contract content differs from lock: ' + name)
    contract = json.loads((TARGET / 'workflow-v1.json').read_text())
    schema = json.loads((ROOT / 'spec/template-v4.schema.json').read_text())
    operations = schema['properties']['workflows']['additionalProperties']['properties']['required_operations']['items']['enum']
    if operations != list(contract['operations']):
        raise ValueError('template operation vocabulary differs from shared contract')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--source', type=Path, help='Explicit checkout contracts directory')
    parser.add_argument('--revision', help='Full committed source revision')
    args = parser.parse_args()
    if args.check:
        verify()
        print('Workflow contract lock: PASS')
        return 0
    if args.source is None or not args.revision or not re.fullmatch('[0-9a-f]{40}', args.revision):
        parser.error('synchronization requires --source and a full --revision')
    source = args.source.resolve()
    repository = Path(subprocess.check_output(['git', '-C', str(source), 'rev-parse', '--show-toplevel'], text=True).strip())
    contents = {}
    for name in FILES:
        data = (source / name).read_bytes()
        committed = subprocess.check_output(['git', '-C', str(repository), 'show', args.revision + ':' + (source / name).relative_to(repository).as_posix()])
        if data != committed:
            raise ValueError('source must match exact committed contract: ' + name)
        json.loads(data)
        contents[name] = data
    TARGET.mkdir(parents=True, exist_ok=True)
    for name, data in contents.items():
        (TARGET / name).write_bytes(data)
    lock = {'repository': 'https://github.com/Alibaba-Agent-Sandbox/python-sdk', 'revision': args.revision,
            'files': {name: hashlib.sha256(data).hexdigest() for name, data in contents.items()}}
    LOCK.write_text(json.dumps(lock, indent=2) + '\n')
    verify()
    print('Workflow contracts synchronized and verified')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
