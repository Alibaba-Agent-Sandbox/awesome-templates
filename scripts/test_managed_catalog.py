"""Managed inputs keep historical evidence without manufacturing current certification."""
import copy
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
    row = {'name': 'external', 'provider': 'e2b', 'template_id': 'desktop', 'kind': 'provider-managed',
           'documentation': 'docs/managed/external/README.md', 'historical_evidence': ['proof.json'],
           'spec_version': 4, 'workflow_contract_version': 1, 'provides': {}, 'default_workflow': 'exec',
           'workflows': {'exec': {'kind': 'exec', 'input': 'managed', 'startup': 'none',
                                  'binding': {'transport': 'exec', 'endpoint': 'provider-native', 'caller': 'host', 'authentication': 'provider'},
                                  'operation': 'exec.run', 'required_operations': []}}}
    proof = {'template': 'external', 'provider': 'e2b', 'template_id': 'desktop', 'passed': False, 'status': 'NOT_VERIFIED'}
    return row, proof


def write(root, row, proof):
    (root / 'awesome-templates.yaml').write_text(yaml.safe_dump({'schema_version': 2, 'templates': [{'name': 'source', 'path': 'source'}], 'managed_templates': [row]}))
    (root / 'proof.json').write_text(json.dumps(proof))


def test_managed_workflow_is_not_a_buildable_source(tmp_path):
    row, proof = fixture(tmp_path)
    write(tmp_path, row, proof)
    assert check(tmp_path) == []
    names = catalog_names(tmp_path)
    assert names == ['source'] and select(names, ['docs/managed/external/README.md']) == []
    with pytest.raises(ValueError):
        select(names, [], requested='external')


@pytest.mark.parametrize('change', ['claim', 'provider', 'identity', 'fields', 'docs', 'default', 'source-input', 'unknown-operation', 'old-schema'])
def test_invalid_workflow_or_retired_claim_is_rejected(tmp_path, change):
    row, proof = fixture(tmp_path)
    if change == 'claim': row['native_interpreter_verified'] = True
    elif change == 'provider': row['provider'] = 'unknown'
    elif change == 'identity': proof['template'] = 'another'
    elif change == 'fields': row['path'] = 'external'
    elif change == 'docs': (tmp_path / 'docs/managed/external/README.zh-CN.md').unlink()
    elif change == 'default': row['default_workflow'] = 'missing'
    elif change == 'source-input': row['workflows']['exec']['input'] = 'source'
    elif change == 'unknown-operation': row['workflows']['exec']['required_operations'] = ['code.interpret']
    elif change == 'old-schema': row['spec_version'] = 3
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
    row['provider'] = {}
    write(tmp_path, row, proof)
    assert check(tmp_path)
    row['provider'] = 'e2b'
    row['historical_evidence'] = 'proof.json'
    write(tmp_path, row, proof)
    assert check(tmp_path)


def test_managed_application_requires_its_selected_service_operation(tmp_path):
    row, proof = fixture(tmp_path)
    row['provides'] = {'app': {'protocol': 'agent-sandbox-server', 'version': 2,
                               'port': 9000, 'operations': ['commands.list']}}
    row['workflows']['exec'] = {
        'kind': 'application', 'input': 'managed', 'startup': 'none', 'service': 'app',
        'binding': {'transport': 'http', 'endpoint': 'provider-port',
                    'caller': 'host', 'authentication': 'service-token'},
        'operation': 'commands.run', 'required_operations': [],
    }
    write(tmp_path, row, proof)
    assert any('operation is not provided' in problem for problem in check(tmp_path))
    row['provides']['app']['operations'].append('commands.run')
    write(tmp_path, row, proof)
    assert check(tmp_path) == []


@pytest.mark.parametrize('kind', ['exec', 'interpreter'])
def test_managed_non_application_cannot_bind_a_service(tmp_path, kind):
    row, proof = fixture(tmp_path)
    workflow = row['workflows']['exec']
    workflow['service'] = 'app'
    if kind == 'interpreter':
        workflow.update(kind='interpreter', operation='code.default-context.execute')
        workflow['binding']['transport'] = 'http'
    write(tmp_path, row, proof)
    assert any('service only applies to application' in problem for problem in check(tmp_path))


def test_managed_exec_startup_requires_an_explicit_command(tmp_path):
    row, proof = fixture(tmp_path)
    row['workflows']['exec']['startup'] = 'exec'
    write(tmp_path, row, proof)
    assert any('exec startup needs an explicit start_cmd' in problem for problem in check(tmp_path))
