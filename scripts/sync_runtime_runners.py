#!/usr/bin/env python3
"""Generate standalone business startup scripts; never add runtime fields to resource YAML."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    source = (ROOT / 'scripts/runtime_runner.py').read_text()
    checks = json.loads((ROOT / 'scripts/template-checks.json').read_text())['templates']
    failed = []
    for name, expected in checks.items():
        runtime = expected.get('runtime')
        if not runtime:
            continue
        output = source.replace('START_COMMAND = ""', 'START_COMMAND = ' + repr(runtime['start']))
        output = output.replace('RUNTIME_ENV_NAMES: tuple[str, ...] = ()', 'RUNTIME_ENV_NAMES: tuple[str, ...] = ' + repr(tuple(runtime['envNames'])))
        output = output.replace('# Replaced by sync_runtime_runners.py in each standalone generated script.', '# Generated from scripts/runtime_runner.py; regenerate with scripts/sync_runtime_runners.py.')
        path = ROOT / name / 'run.py'
        if args.check:
            if not path.is_file() or path.read_text() != output:
                failed.append(name)
        else:
            path.write_text(output)
    if failed:
        print('Outdated runtime launchers: ' + ', '.join(failed))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
