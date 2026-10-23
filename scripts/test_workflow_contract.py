"""Workflow paths, unchanged application topology and complete input identity regressions."""
import copy
import hashlib
import json
from pathlib import Path

import pytest
import yaml

from template_application import validate_v4
from manifest_contract import manifest_contract_sha256
from sync_workflow_contracts import verify

ROOT = Path(__file__).resolve().parents[1]


def manifest():
    return yaml.safe_load((ROOT / '_skeleton/template.yaml').read_text())


def test_offline_contract_lock_is_exact():
    verify()


@pytest.mark.parametrize('field', ['capabilities', 'tested_on', 'providers'])
def test_retired_machine_fields_are_rejected(field):
    data = manifest()
    data[field] = []
    assert validate_v4(data)


@pytest.mark.parametrize('mutate', [
    lambda data: data.update(spec_version=3),
    lambda data: data.update(default_workflow='missing'),
    lambda data: data['workflows']['application'].pop('startup'),
    lambda data: data['workflows']['application'].update(unknown=True),
    lambda data: data['workflows']['application']['binding'].update(url='https://arbitrary.invalid'),
    lambda data: data['provides']['app'].update(port=70000),
    lambda data: data['provides']['app'].update(version=9007199254740992),
    lambda data: data['workflows']['application'].update(service='undeclared'),
    lambda data: data['workflows']['application'].update(operation='not.provided'),
    lambda data: data['workflows']['application'].update(required_operations=['code.interpret']),
])
def test_ambiguous_or_unsafe_workflow_input_fails(mutate):
    data = manifest()
    mutate(data)
    assert validate_v4(data)


def test_python_named_service_does_not_declare_unified_interpreter_requirements():
    data = manifest()
    assert validate_v4(data) == []
    workflow = data['workflows']['application']
    assert workflow['kind'] == 'application'
    assert workflow['operation'] == 'commands.run'
    assert not any(operation.startswith('code.') for operation in workflow['required_operations'])


def test_default_change_and_added_workflow_change_manifest_identity():
    data = manifest()
    original = manifest_contract_sha256(yaml.safe_dump(data).encode())
    data['workflows']['other'] = copy.deepcopy(data['workflows']['application'])
    data['workflows']['other']['binding']['caller'] = 'guest'
    other = manifest_contract_sha256(yaml.safe_dump(data).encode())
    assert other != original
    data['default_workflow'] = 'other'
    assert manifest_contract_sha256(yaml.safe_dump(data).encode()) != other


def test_application_hooks_and_durable_state_remain_distinct_from_startup():
    data = yaml.safe_load((ROOT / 'docs/examples/application-external/template.yaml').read_text())
    assert validate_v4(data, ROOT / 'docs/examples/application-external') == []
    assert data['application']['state']['profile'] == 'durable'
    assert data['application']['runtime']['placement'] == 'external'
    assert data['workflows']['application']['startup'] == 'exec'


def test_workflow_can_add_required_checks_without_replacing_profile_minimum():
    data = manifest()
    data['workflows']['application']['required_checks'] = ['model.extra-assertion']
    assert validate_v4(data) == []
    data['workflows']['application']['required_checks'] = ['model.extra-assertion', 'model.extra-assertion']
    assert validate_v4(data)


def test_explicit_portable_build_profile_is_not_an_implicit_source_rewrite():
    source = ROOT / 'python-hello'
    data = yaml.safe_load((source / 'template.yaml').read_text())
    assert validate_v4(data, source) == []
    assert data['build_profiles']['portable'] == {'dockerfile': 'Dockerfile.portable', 'context': '.'}
    assert '<region>' in (source / 'Dockerfile').read_text()
    portable = (source / 'Dockerfile.portable').read_text()
    assert '@sha256:' in portable
    assert 'COPY *.whl' not in portable
    assert 'USER user' in portable
    data['build_profiles']['portable']['context'] = '../foreign'
    assert validate_v4(data, source)


def test_full_schema_accepts_shared_contract_underscore_workflow_id():
    data = manifest()
    data['workflows']['application_image'] = data['workflows'].pop('application')
    data['default_workflow'] = 'application_image'
    assert validate_v4(data) == []


def test_retired_local_runtime_profile_is_rejected():
    data = yaml.safe_load((ROOT / 'docs/examples/application-local/template.yaml').read_text())
    assert validate_v4(data) == []
    data['application']['runtime']['profile'] = 'legacy-codex-agent-api'
    assert validate_v4(data)
