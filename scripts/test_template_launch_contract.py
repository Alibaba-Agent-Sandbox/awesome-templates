"""V1 startup exposes every service without retired workflow selectors."""
from pathlib import Path
import pytest
import yaml
from template_application import validate_manifest
from manifest_contract import manifest_contract_sha256
from sync_launch_contracts import verify
ROOT = Path(__file__).resolve().parents[1]


def manifest():
    return yaml.safe_load((ROOT / '_skeleton/template.yaml').read_text())


def test_shared_launch_contract_is_locked():
    verify()  # Historical runtime transport contract retains its original source identity.


@pytest.mark.parametrize('field', ['capabilities', 'tested_on', 'providers', 'workflow_contract_version', 'default_workflow', 'workflows'])
def test_retired_machine_fields_are_rejected(field):
    data = manifest(); data[field] = []
    assert validate_manifest(data)


def test_old_schema_requires_explicit_migration():
    data = manifest(); data['spec_version'] = 5
    assert validate_manifest(data)


@pytest.mark.parametrize('mutate', [
    lambda sb: sb['services']['app'].update(port=70000),
    lambda sb: sb['services']['app'].update(version=9007199254740992),
    lambda sb: sb['services']['app'].pop('protocol'),
    lambda sb: sb.update(start=''),
    lambda sb: sb.update(ready=''),
])
def test_incomplete_startup_or_services_fail(mutate):
    data = manifest(); mutate(data['sandbox']); assert validate_manifest(data)


def test_multiple_services_do_not_need_workflow_selection_or_duplicate_ports():
    data = manifest(); sb = data['sandbox']; sb['services']['secondary'] = dict(sb['services']['app'], port=9001)
    assert validate_manifest(data) == []
    assert 'ports' not in data  # Typed service ports need no duplicate top-level declaration.


def test_service_may_expose_endpoint_without_named_operations():
    data = manifest(); data['sandbox']['services']['app']['operations'] = []
    assert validate_manifest(data) == []


def test_service_and_startup_change_manifest_identity():
    data = manifest(); original = manifest_contract_sha256(yaml.safe_dump(data).encode())
    data['sandbox']['start'] += ' --host 0.0.0.0'
    assert manifest_contract_sha256(yaml.safe_dump(data).encode()) != original
    original = manifest_contract_sha256(yaml.safe_dump(data).encode())
    data['sandbox']['services']['app']['operations'].append('commands.schema')
    assert manifest_contract_sha256(yaml.safe_dump(data).encode()) != original


def test_native_serving_and_managed_application_have_distinct_intent():
    data = yaml.safe_load((ROOT / 'docs/examples/application-external/template.yaml').read_text())
    assert validate_manifest(data) == []
    assert 'application' not in data
    assert data['deployment']['resources']['api']['component'] == 'fc3@0.1.26'


def test_explicit_portable_profile_preserves_default_recipe():
    source = ROOT / 'python-hello'; data = yaml.safe_load((source / 'template.yaml').read_text())
    assert validate_manifest(data, source) == []
    assert data['sandbox']['template']['source']['profiles']['portable'] == {'dockerfile': 'Dockerfile.portable', 'context': '.'}
    assert '<region>' in (source / 'Dockerfile').read_text()
    portable = (source / 'Dockerfile.portable').read_text()
    assert '@sha256:' in portable and 'COPY *.whl' not in portable and 'USER user' in portable


def test_retired_local_profile_is_rejected():
    data = manifest(); data['application'] = {'runtime': {'profile': 'legacy-codex-agent-api'}}
    assert validate_manifest(data)
