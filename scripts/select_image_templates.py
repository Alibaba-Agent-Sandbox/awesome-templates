#!/usr/bin/env python3
"""Select actual changed image contexts or explicit dispatch targets, never credentials."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import subprocess
import yaml

ROOT = Path(__file__).resolve().parents[1]
SHARED_INPUTS = {'.github/workflows/image-build.yml', 'scripts/select_image_templates.py'}


def catalog_names(root: Path = ROOT) -> list[str]:
    names = [item['path'] for item in yaml.safe_load((root/'awesome-templates.yaml').read_text())['templates']]
    if len(set(names)) != len(names) or not all(re.fullmatch(r'[a-z0-9][a-z0-9-]*', name) for name in names):
        raise ValueError('catalog template paths must be unique plain template names')
    return sorted(names)


def select(names: list[str], changed: list[str], requested: str | None = None) -> list[str]:
    if requested is not None:
        selected = [part.strip() for part in requested.split(',')]
        if not selected or any(not name or name not in names for name in selected):
            raise ValueError('dispatch templates must be comma-separated catalog names')
        return sorted(set(selected))
    if SHARED_INPUTS.intersection(changed):
        return names
    selected = set()
    for filename in changed:
        parts = Path(filename).parts
        if len(parts) < 2 or parts[0] not in names:
            continue
        relative = Path(*parts[1:])
        # Prose/evidence is not a runtime input in this catalog. Select all other
        # template files conservatively, including smoke/regression helpers.
        if parts[1] == 'evidence' or relative.suffix.lower() == '.md':
            continue
        selected.add(parts[0])
    return sorted(selected)


def export_all_selected(root: Path = ROOT) -> bool:
    policy = root / '.github/image-export-policy.json'
    if not policy.exists():
        return False
    value = json.loads(policy.read_text())
    if not isinstance(value, dict) or value.get('automatic') not in {'default', 'all-selected'}:
        raise ValueError('automatic image export policy must be default or all-selected')
    if value['automatic'] == 'all-selected' and not str(value.get('reason', '')).strip():
        raise ValueError('all-selected export requires an explicit task reason')
    return value['automatic'] == 'all-selected'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--event', choices=['pull_request','push','workflow_dispatch'])
    parser.add_argument('--base', default='')
    parser.add_argument('--head', default='HEAD')
    parser.add_argument('--templates', default='python-hello')
    parser.add_argument('--export-policy', action='store_true')
    args = parser.parse_args()
    if args.export_policy:
        print('true' if export_all_selected(ROOT) else 'false')
        return 0
    if not args.event:
        parser.error('--event is required for image selection')
    names = catalog_names()
    if args.event == 'workflow_dispatch':
        result = select(names, [], args.templates)
    elif args.event == 'push':
        result = names  # Preserve main's complete gate without trusted prior input-hash evidence.
    elif not args.base or set(args.base) == {'0'}:
        result = names  # A new branch/root revision has no safe comparison.
    else:
        # Git arguments are array elements; no event field is evaluated by a shell.
        try:
            data = subprocess.check_output(['git','diff','--name-only','-z',args.base,args.head,'--'], cwd=ROOT)
        except subprocess.CalledProcessError:
            result = names  # Unavailable comparison history cannot justify skipping an image.
        else:
            result = select(names, [item for item in data.decode().split('\0') if item])
    print(json.dumps(result, separators=(',',':')))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
