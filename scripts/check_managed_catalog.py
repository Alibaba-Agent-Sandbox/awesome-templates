#!/usr/bin/env python3
"""Validate managed template references. Historical receipts never confer certification."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

from check_template import README_EN, README_ZH, PROVIDERS


ROOT = Path(__file__).resolve().parents[1]
SERVICE_FIELDS = {'provides'}
FIELDS = {'name', 'kind', 'documentation', 'historical_evidence', 'resource', 'registry'}


def local_file(root, value):
    if not isinstance(value, str) or not value:
        return None
    path = root / value
    if Path(value).is_absolute() or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
        return None
    return path


def check(root=ROOT):
    problems = []
    try:
        catalog = yaml.safe_load((root / 'awesome-templates.yaml').read_text())
    except (OSError, ValueError, yaml.YAMLError):
        return ['invalid catalog YAML']
    if not isinstance(catalog, dict) or catalog.get('schema_version') != 3:
        return ['catalog requires schema_version: 3']
    rows = catalog.get('managed_templates', [])
    if not isinstance(rows, list):
        return ['managed_templates must be a list']
    from template_application import validate_manifest, _profile_module, _VALIDATOR, _REGISTRY_VALIDATOR
    source_names = {item.get('name') for item in catalog.get('templates', []) if isinstance(item, dict) and isinstance(item.get('name'), str)}
    seen = set()
    for index, row in enumerate(rows):
        label = str(row.get('name', index)) if isinstance(row, dict) else str(index)
        def fail(message):
            problems.append(label + ': ' + message)
        if not isinstance(row, dict) or set(row) != FIELDS:
            fail('managed fields must match the current template contract')
            continue
        name = row['name']
        resource = row.get('resource', {})
        resource_errors = validate_manifest(resource)
        for message in resource_errors:
            fail('resource: ' + message)
        if resource_errors:
            continue
        sandbox = resource.get('sandbox', {}) if isinstance(resource, dict) else {}
        provider = sandbox.get('provider')
        if not isinstance(name, str) or not re.fullmatch('[a-z0-9][a-z0-9-]*', name):
            fail('name must be kebab-case')
            continue
        if name in seen or name in source_names:
            fail('name duplicates a source/managed entry')
        seen.add(name)
        if not isinstance(provider, str) or provider not in PROVIDERS:
            fail('unknown provider')
        native = sandbox.get('template', {})
        if row['kind'] != 'provider-managed' or not isinstance(native.get('reference'), str) or any(key in native for key in ('source', 'image')):
            fail('managed kind/native template reference required')
        if resource.get('name') != name:
            fail('resource name differs from catalog identity')
        metadata_path = local_file(root, row['registry'])
        if not metadata_path:
            fail('registry must reference existing publication metadata')
        else:
            try:
                metadata = _profile_module.normalize_registry_v1(yaml.safe_load(metadata_path.read_text()), resource, _REGISTRY_VALIDATOR, _VALIDATOR)
                if metadata['name'] != name:
                    fail('publication identity differs from native resource')
                for language, value in metadata['readme'].items():
                    if not local_file(metadata_path.parent, value):
                        fail('publication README is missing or outside its source')
            except (OSError, TypeError, ValueError):
                fail('invalid managed publication metadata')
        doc = local_file(root, row['documentation'])
        if not doc:
            fail('documentation must be an existing local file')
        else:
            for file, headings in [(doc, README_EN), (doc.with_name('README.zh-CN.md'), README_ZH)]:
                if not file.is_file():
                    fail('bilingual README missing')
                    continue
                actual = [line[3:].strip() for line in file.read_text().splitlines() if line.startswith('## ')]
                if tuple(actual) != headings:
                    fail('managed README requires the ordered 12 consumer sections')
        history = row['historical_evidence']
        if not isinstance(history, list) or not history or not all(isinstance(item, str) for item in history):
            fail('historical_evidence must list original receipt paths')
            continue
        for reference in history:
            evidence = local_file(root, reference)
            if not evidence:
                fail('historical evidence must be an existing local file')
                continue
            try:
                proof = json.loads(evidence.read_text())
            except (OSError, ValueError):
                fail('invalid historical evidence JSON')
                continue
            if not isinstance(proof, dict):
                fail('historical evidence must be an object')
            elif proof.get('provider') != provider or proof.get('template') != name:
                fail('historical evidence provider/template differs')
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    problems = check(parser.parse_args().root)
    for problem in problems:
        print(problem)
    print(f'Managed catalog: {len(problems)} violations; historical records do not certify current launches')
    return int(bool(problems))


if __name__ == '__main__':
    raise SystemExit(main())
