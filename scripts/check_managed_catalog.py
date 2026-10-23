#!/usr/bin/env python3
"""Validate managed workflow inputs. Historical receipts never confer certification."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from check_template import README_EN, README_ZH, PROVIDERS

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_FIELDS = {'workflow_contract_version', 'provides', 'default_workflow', 'workflows'}
FIELDS = {'name', 'provider', 'template_id', 'kind', 'documentation', 'historical_evidence', 'spec_version'} | WORKFLOW_FIELDS


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
    if not isinstance(catalog, dict) or catalog.get('schema_version') != 2:
        return ['catalog requires schema_version: 2']
    rows = catalog.get('managed_templates', [])
    if not isinstance(rows, list):
        return ['managed_templates must be a list']
    schema = json.loads((ROOT / 'spec/workflow-portion.schema.json').read_text())
    validator = Draft202012Validator(schema)
    source_names = {item.get('name') for item in catalog.get('templates', []) if isinstance(item, dict) and isinstance(item.get('name'), str)}
    seen = set()
    for index, row in enumerate(rows):
        label = str(row.get('name', index)) if isinstance(row, dict) else str(index)
        def fail(message):
            problems.append(label + ': ' + message)
        if not isinstance(row, dict) or set(row) != FIELDS:
            fail('managed fields must match the current workflow contract')
            continue
        name, provider = row['name'], row['provider']
        if not isinstance(name, str) or not re.fullmatch('[a-z0-9][a-z0-9-]*', name):
            fail('name must be kebab-case')
            continue
        if name in seen or name in source_names:
            fail('name duplicates a source/managed entry')
        seen.add(name)
        if not isinstance(provider, str) or provider not in PROVIDERS:
            fail('unknown provider')
        if row['spec_version'] != 4 or type(row['spec_version']) is not int:
            fail('managed workflow requires spec_version: 4')
        if row['kind'] != 'provider-managed' or not isinstance(row['template_id'], str) or not row['template_id'].strip():
            fail('managed kind/native template ID required')
        portion = {key: row[key] for key in WORKFLOW_FIELDS}
        errors = list(validator.iter_errors(portion))
        for error in errors:
            fail('workflow: ' + error.message)
        if not errors:
            if row['default_workflow'] not in row['workflows']:
                fail('default_workflow must name an existing workflow')
            for workflow_id, workflow in row['workflows'].items():
                if workflow['input'] != 'managed':
                    fail(f'{workflow_id}: managed records require managed input')
                if workflow['kind'] == 'application' and workflow['service'] not in row['provides']:
                    fail(f'{workflow_id}: undeclared service')
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
                    fail('managed README requires the ordered 14 sections')
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
    print(f'Managed catalog: {len(problems)} violations; historical records do not certify current workflows')
    return int(bool(problems))


if __name__ == '__main__':
    raise SystemExit(main())
