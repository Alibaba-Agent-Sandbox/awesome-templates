"""Static resource admission stays separate from business startup and historical receipts."""
from pathlib import Path
import pytest
import yaml
from template_application import validate_manifest
from manifest_contract import manifest_contract_sha256
from sync_launch_contracts import verify
ROOT = Path(__file__).resolve().parents[1]


def manifest():
    return yaml.safe_load((ROOT / '_skeleton/template.yaml').read_text())


def test_historical_launch_contract_is_locked():
    verify()


@pytest.mark.parametrize('field', ['capabilities','tested_on','providers','workflow_contract_version','default_workflow','workflows','application','deployment','instance','parameters'])
def test_removed_machine_fields_are_rejected(field):
    data=manifest();data[field]={}
    assert validate_manifest(data)


def test_old_schema_requires_explicit_migration():
    data=manifest();data['spec_version']=5
    assert validate_manifest(data)


@pytest.mark.parametrize('field', ['services','instance','start','ready'])
def test_dynamic_fields_do_not_return_under_named_resource(field):
    data=manifest();data['sandbox']['agent'][field]={}
    assert validate_manifest(data)


def test_multiple_resources_have_independent_templates_and_global_names():
    import copy
    data=manifest();data['sandbox']['other']=copy.deepcopy(data['sandbox']['agent'])
    assert validate_manifest(data)==[]
    data['serving']={'agent':{'component':'serverless-devs/fc3@0.1.26','props':{}}}
    assert validate_manifest(data)


def test_template_and_serving_changes_change_manifest_identity():
    data=manifest();original=manifest_contract_sha256(yaml.safe_dump(data).encode())
    data['sandbox']['agent']['template']['cpu']=4
    assert manifest_contract_sha256(yaml.safe_dump(data).encode())!=original
    original=manifest_contract_sha256(yaml.safe_dump(data).encode())
    data['serving']={'api':{'component':'serverless-devs/fc3@0.1.26','props':{'functionName':'example'}}}
    assert manifest_contract_sha256(yaml.safe_dump(data).encode())!=original


def test_native_serving_has_no_business_profile_wrapper():
    data=yaml.safe_load((ROOT/'docs/examples/application-external/template.yaml').read_text())
    assert validate_manifest(data)==[]
    assert 'application' not in data and 'deployment' not in data
    assert data['serving']['api']['component']=='serverless-devs/fc3@0.1.26'


def test_portable_recipe_is_selected_by_buildconfig():
    source=ROOT/'python-hello';data=yaml.safe_load((source/'template.yaml').read_text())
    assert data['sandbox']['agent']['template']['buildConfig']['dockerfile']=='Dockerfile'
    data['sandbox']['agent']['template']['buildConfig']['dockerfile']='Dockerfile.portable'
    assert validate_manifest(data,source)==[]
    portable=(source/'Dockerfile.portable').read_text()
    assert '@sha256:' in portable and 'COPY *.whl' not in portable and 'USER user' in portable
