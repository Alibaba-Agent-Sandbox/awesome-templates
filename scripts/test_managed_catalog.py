"""Managed inputs keep historical evidence without manufacturing current certification."""
import json

import pytest
import yaml

from check_managed_catalog import check, README_EN, README_ZH
from select_image_templates import catalog_names, select


def fixture(tmp_path):
    doc = tmp_path / 'docs/managed/external'
    doc.mkdir(parents=True)
    for name, headings in [('README.md', README_EN), ('README.zh-CN.md', README_ZH)]:
        (doc / name).write_text('# external\n\n' + '\n\n'.join('## ' + heading + '\n\nScoped content.' for heading in headings) + '\n')
    row = {'name': 'external', 'kind': 'provider-managed',
           'documentation': 'docs/managed/external/README.md', 'historical_evidence': ['proof.json'],
           'registry': 'docs/managed/external/registry.yaml', 'resource': {'specVersion': 1, 'name': 'external', 'sandbox': {'agent': {'provider': 'e2b', 'template': {'reference': 'desktop'}}}}}
    (doc / 'registry.yaml').write_text(yaml.safe_dump({'specVersion': 1, 'name': 'external', 'version': 'provider-managed', 'description': {'en': 'Native desktop', 'zh': '原生桌面'}, 'author': 'example', 'license': 'Apache-2.0', 'readme': {'en': 'README.md', 'zh': 'README.zh-CN.md'}}))
    proof = {'template': 'external', 'provider': 'e2b', 'passed': False, 'status': 'NOT_VERIFIED'}
    return row, proof


def write(root, row, proof):
    (root / 'awesome-templates.yaml').write_text(yaml.safe_dump({'schema_version': 3, 'templates': [{'name': 'source', 'path': 'source'}], 'managed_templates': [row]}))
    (root / 'proof.json').write_text(json.dumps(proof))


def test_managed_reference_is_not_a_buildable_source(tmp_path):
    row, proof = fixture(tmp_path)
    write(tmp_path, row, proof)
    assert check(tmp_path) == []
    names = catalog_names(tmp_path)
    assert names == ['source'] and select(names, ['docs/managed/external/README.md']) == []
    with pytest.raises(ValueError):
        select(names, [], requested='external')


@pytest.mark.parametrize('change', ['claim', 'provider', 'identity', 'fields', 'docs', 'retired-workflow', 'invalid-service', 'old-schema'])
def test_invalid_reference_or_retired_claim_is_rejected(tmp_path, change):
    row, proof = fixture(tmp_path)
    if change == 'claim': row['native_interpreter_verified'] = True
    elif change == 'provider': row['resource']['sandbox']['agent']['provider'] = 'unknown'
    elif change == 'identity': proof['template'] = 'another'
    elif change == 'fields': row['path'] = 'external'
    elif change == 'docs': (tmp_path / 'docs/managed/external/README.zh-CN.md').unlink()
    elif change == 'retired-workflow': row['workflows'] = {}
    elif change == 'invalid-service': row['resource']['sandbox']['services'] = {'app': {'port': 70000}}
    elif change == 'old-schema': row['resource']['specVersion'] = 4
    write(tmp_path, row, proof)
    assert check(tmp_path)


def test_handwritten_pass_remains_historical_and_cannot_add_a_certification_claim(tmp_path):
    row, proof = fixture(tmp_path)
    proof.update(passed=True, cleanup_verified=True, checks=['invented pass'], trusted=True)
    write(tmp_path, row, proof)
    assert check(tmp_path) == []  # The catalog validates a historical link, never derives certification.
    row['verified'] = True
    write(tmp_path, row, proof)
    assert check(tmp_path)


@pytest.mark.parametrize('value', [None, [], False, 'invalid', {'schema_version': 1}])
def test_old_or_invalid_catalog_is_a_validation_failure(tmp_path, value):
    (tmp_path / 'awesome-templates.yaml').write_text(yaml.safe_dump(value))
    assert check(tmp_path)


def test_untyped_provider_or_history_cannot_bypass_validation(tmp_path):
    row, proof = fixture(tmp_path)
    row['resource']['sandbox']['agent']['provider'] = {}
    write(tmp_path, row, proof)
    assert check(tmp_path)
    row['resource']['sandbox']['agent']['provider'] = 'e2b'
    row['historical_evidence'] = 'proof.json'
    write(tmp_path, row, proof)
    assert check(tmp_path)


def test_managed_resource_rejects_removed_public_services_layer(tmp_path):
    row, proof = fixture(tmp_path)
    row['resource']['sandbox']['services'] = {'app': {'protocol': 'agent-sandbox-server', 'version': 2,
                              'port': 9000, 'operations': ['commands.list', 'commands.run']}}
    write(tmp_path, row, proof)
    assert check(tmp_path)
    row['resource']['sandbox']['services']['app']['port'] = 70000
    write(tmp_path, row, proof)
    assert check(tmp_path)


@pytest.mark.parametrize('sandbox', [None, [], False, 'invalid'])
def test_malformed_native_resource_is_reported_without_projection_crash(tmp_path, sandbox):
    row, proof = fixture(tmp_path)
    row['resource']['sandbox'] = sandbox
    write(tmp_path, row, proof)
    assert any('resource:' in item for item in check(tmp_path))
