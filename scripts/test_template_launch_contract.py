"""One template startup keeps every service and rejects retired workflow selectors."""
import json
from pathlib import Path

import pytest
import yaml

from template_application import validate_v5
from manifest_contract import manifest_contract_sha256
from sync_launch_contracts import verify

ROOT = Path(__file__).resolve().parents[1]


def test_shared_launch_contract_is_locked():
    verify()


def manifest():
    return yaml.safe_load((ROOT / '_skeleton/template.yaml').read_text())


@pytest.mark.parametrize('field', ['capabilities', 'tested_on', 'providers', 'workflow_contract_version', 'default_workflow', 'workflows'])
def test_retired_machine_fields_are_rejected(field):
    data = manifest()
    data[field] = []
    assert validate_v5(data)


def test_old_schema_requires_explicit_migration():
    data = manifest()
    data['spec_version'] = 4
    assert 'migrate' in validate_v5(data)[0]


@pytest.mark.parametrize('mutate', [
    lambda data: data['provides']['app'].update(port=70000),
    lambda data: data['provides']['app'].update(version=9007199254740992),
    lambda data: data['provides']['app'].pop('protocol'),
    lambda data: data.update(start_cmd=''),
    lambda data: data.update(ready_cmd=''),
])
def test_incomplete_startup_or_services_fail(mutate):
    data = manifest()
    mutate(data)
    assert validate_v5(data)


def test_multiple_provided_services_do_not_need_workflow_selection():
    data = manifest()
    data['ports'].append(9001)
    data['provides']['secondary'] = dict(data['provides']['app'], port=9001)
    assert validate_v5(data) == []
    data['ports'].remove(9001)
    assert any('must be declared in ports' in error for error in validate_v5(data))


def test_service_may_expose_an_endpoint_without_named_operations():
    data = manifest()
    data['provides']['app']['operations'] = []
    assert validate_v5(data) == []


def test_service_and_startup_changes_change_manifest_identity():
    data = manifest()
    original = manifest_contract_sha256(yaml.safe_dump(data).encode())
    data['start_cmd'] += ' --host 0.0.0.0'
    assert manifest_contract_sha256(yaml.safe_dump(data).encode()) != original
    original = manifest_contract_sha256(yaml.safe_dump(data).encode())
    data['provides']['app']['operations'].append('commands.schema')
    assert manifest_contract_sha256(yaml.safe_dump(data).encode()) != original


def test_application_hooks_and_durable_state_remain_distinct_from_startup():
    data = yaml.safe_load((ROOT / 'docs/examples/application-external/template.yaml').read_text())
    assert validate_v5(data, ROOT / 'docs/examples/application-external') == []
    assert data['application']['state']['profile'] == 'durable'
    assert data['application']['runtime']['placement'] == 'external'
    assert data['start_cmd']


def test_explicit_portable_build_profile_preserves_the_default_recipe():
    source = ROOT / 'python-hello'
    data = yaml.safe_load((source / 'template.yaml').read_text())
    assert validate_v5(data, source) == []
    assert data['build_profiles']['portable'] == {'dockerfile': 'Dockerfile.portable', 'context': '.'}
    assert '<region>' in (source / 'Dockerfile').read_text()
    portable = (source / 'Dockerfile.portable').read_text()
    assert '@sha256:' in portable
    assert 'COPY *.whl' not in portable
    assert 'USER user' in portable


def test_retired_local_runtime_profile_is_rejected():
    data = yaml.safe_load((ROOT / 'docs/examples/application-local/template.yaml').read_text())
    assert validate_v5(data) == []
    data['application']['runtime']['profile'] = 'legacy-codex-agent-api'
    assert validate_v5(data)
