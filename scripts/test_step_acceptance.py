"""Reject stale/misattributed acceptance even when its top-level pass is true."""
import hashlib
import subprocess

from manifest_contract import manifest_contract_sha256

import pytest

from step_acceptance import inspect_http_receipt, inspect_receipt


def example(tmp_path):
    (tmp_path / "template.yaml").write_text("name: example\nversion: 1.0.0\nsmoke: [{command: hello}]\n")
    for name in ["Dockerfile", "commands.py", "requirements.lock"]:
        (tmp_path / name).write_text(name)
    return {"provider": "alicloud-express", "build_mode": "steps", "passed": True,
            "cleanup_verified": True, "template_version": "1.0.0",
            "commands": [{"name": "hello", "via": via, "ok": True} for via in ("cli", "sdk")],
            "build_provenance": {"source_manifest_contract_sha256": manifest_contract_sha256((tmp_path / "template.yaml").read_bytes()), "inputs_sha256": {
                name: hashlib.sha256((tmp_path / name).read_bytes()).hexdigest()
                for name in ["Dockerfile", "commands.py", "requirements.lock", "template.yaml"]}}}


@pytest.mark.parametrize("field,value", [("template_version", "0.9.0"), ("build_mode", "image"),
    ("cleanup_verified", False), ("passed", False), ("provider", "different-provider")])
def test_success_from_another_scope_or_uncertain_cleanup_is_rejected(tmp_path, field, value):
    receipt = example(tmp_path)
    receipt[field] = value
    assert not inspect_receipt(tmp_path, receipt)[0]


@pytest.mark.parametrize("name", ["Dockerfile", "commands.py", "requirements.lock"])
def test_changed_runtime_cannot_inherit_acceptance(tmp_path, name):
    receipt = example(tmp_path)
    assert inspect_receipt(tmp_path, receipt)[0]
    (tmp_path / name).write_text("new runtime bytes")
    assert not inspect_receipt(tmp_path, receipt)[0]


def test_retired_qualification_metadata_invalidates_runtime_receipt(tmp_path):
    receipt = example(tmp_path)
    (tmp_path / "template.yaml").write_text("name: example\nversion: 1.0.0\nsmoke: [{command: hello}]\ntested_on: [alicloud-express]\n")
    assert not inspect_receipt(tmp_path, receipt)[0]


def test_sdk_only_call_does_not_certify_cli(tmp_path):
    receipt = example(tmp_path)
    receipt["commands"] = [receipt["commands"][1]]
    assert not inspect_receipt(tmp_path, receipt)[0]


def test_different_smoke_arguments_require_new_calls(tmp_path):
    receipt = example(tmp_path)
    (tmp_path / "template.yaml").write_text("name: example\nversion: 1.0.0\nsmoke: [{command: hello, args: {name: new-input}}]\n")
    assert not inspect_receipt(tmp_path, receipt)[0]


def test_private_cache_must_be_independently_cleaned(tmp_path):
    receipt = example(tmp_path)
    receipt["build_provenance"]["asset_transport"] = "oss"
    assert not inspect_receipt(tmp_path, receipt)[0]
    receipt["asset_cache"] = {"private_acl_verified": True, "cleanup_verified": True}
    assert inspect_receipt(tmp_path, receipt)[0]


@pytest.mark.parametrize("nested", [True, False])
def test_full_http_is_separate_from_cli_sdk_smoke_and_retains_model_skip(tmp_path, nested):
    receipt = example(tmp_path)
    (tmp_path / "e2e_test.py").write_text("original external controller")
    counts = {"controller_sha256": hashlib.sha256((tmp_path / "e2e_test.py").read_bytes()).hexdigest(),
              "pass_count": 7, "fail_count": 0, "skip_count": 1, "exit_code": 0}
    receipt.pop("commands")
    if nested:
        receipt["http_acceptance"] = counts
    else:
        counts["http_exit_code"] = counts.pop("exit_code")
        receipt.update(counts)
    assert inspect_http_receipt(tmp_path, receipt)[0]
    assert not inspect_receipt(tmp_path, receipt)[0]
    (tmp_path / "e2e_test.py").write_text("changed controller")
    assert not inspect_http_receipt(tmp_path, receipt)[0]


@pytest.mark.parametrize("field,value", [("exit_code", 1), ("fail_count", 1), ("pass_count", 0),
                                        ("pass_count", True), ("controller_sha256", "0" * 64)])
def test_failed_or_misattributed_full_http_cannot_pass(tmp_path, field, value):
    receipt = example(tmp_path)
    (tmp_path / "e2e_test.py").write_text("original controller")
    receipt["http_acceptance"] = {"controller_sha256": hashlib.sha256((tmp_path / "e2e_test.py").read_bytes()).hexdigest(),
                                  "pass_count": 1, "fail_count": 0, "exit_code": 0}
    assert inspect_http_receipt(tmp_path, receipt)[0]
    receipt["http_acceptance"][field] = value
    assert not inspect_http_receipt(tmp_path, receipt)[0]


def test_gateway_lifecycle_skip_cannot_be_full_acceptance(tmp_path):
    source = tmp_path / "openclaw"
    source.mkdir()
    receipt = example(source)
    (source / "e2e_test.py").write_text("original lifecycle controller")
    receipt["http_acceptance"] = {"exit_code": 0, "pass_count": 5, "fail_count": 0, "skip_count": 2,
                                  "controller_sha256": hashlib.sha256((source / "e2e_test.py").read_bytes()).hexdigest()}
    assert not inspect_http_receipt(source, receipt)[0]
    receipt["build_provenance"]["test_configuration"] = {"gateway_lifecycle_required": True}
    assert not inspect_http_receipt(source, receipt)[0]
    receipt["http_acceptance"].update(pass_count=11, skip_count=1)
    assert inspect_http_receipt(source, receipt)[0]

@pytest.mark.parametrize('change',[
 'start_cmd: changed-launch\n','ready_cmd: changed-readiness\n','resources: {cpu: 2, memory: 8192}\n',
 'env: {SAFE: changed}\n','ports: [9000, 9100]\n','base: changed-base\n','capabilities: [shell]\n',
])
def test_same_version_changed_manifest_contract_rejects_old_cloud_success(tmp_path,change):
    receipt=example(tmp_path)
    assert inspect_receipt(tmp_path,receipt)[0]
    path=tmp_path/'template.yaml';path.write_text(path.read_text()+change)
    assert not inspect_receipt(tmp_path,receipt)[0]


def init_history(source):
    subprocess.run(['git','init','-q',str(source)],check=True)
    subprocess.run(['git','-C',str(source),'add','template.yaml'],check=True)
    subprocess.run(['git','-C',str(source),'-c','user.name=Manifest Fixture','-c','user.email=manifest@example.invalid','commit','-qm','fixture manifest'],check=True)
    return subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()

@pytest.mark.parametrize('recorded_revision',[True,False])
def test_legacy_metadata_update_requires_exact_original_historical_bytes(tmp_path,recorded_revision):
    receipt=example(tmp_path);proof=receipt['build_provenance'];proof.pop('source_manifest_contract_sha256')
    revision=init_history(tmp_path)
    if recorded_revision:proof['copy_source_commit']=revision
    path=tmp_path/'template.yaml';path.write_text(path.read_text()+'tested_on: [alicloud-express]\n')
    assert not inspect_receipt(tmp_path,receipt)[0]
    path.write_text(path.read_text()+'start_cmd: changed-contract\n')
    assert not inspect_receipt(tmp_path,receipt)[0]


def test_legacy_unchanged_exact_manifest_does_not_need_git_history(tmp_path):
    receipt=example(tmp_path);receipt['build_provenance'].pop('source_manifest_contract_sha256')
    assert inspect_receipt(tmp_path,receipt)[0]


def test_legacy_qualification_change_without_history_is_missing(tmp_path):
    receipt=example(tmp_path);receipt['build_provenance'].pop('source_manifest_contract_sha256')
    path=tmp_path/'template.yaml';path.write_text(path.read_text()+'tested_on: [alicloud-express]\n')
    assert not inspect_receipt(tmp_path,receipt)[0]

@pytest.mark.parametrize('bad',['0'*40,'HEAD','-option',None])
def test_legacy_mismatched_revision_or_raw_digest_cannot_inherit_pass(tmp_path,bad):
    receipt=example(tmp_path);proof=receipt['build_provenance'];proof.pop('source_manifest_contract_sha256');init_history(tmp_path)
    if bad is None:proof['inputs_sha256']['template.yaml']='0'*64
    else:proof['copy_source_commit']=bad
    path=tmp_path/'template.yaml';path.write_text(path.read_text()+'tested_on: [alicloud-express]\n')
    assert not inspect_receipt(tmp_path,receipt)[0]

@pytest.mark.parametrize('missing',[True,False])
def test_missing_or_changed_manifest_hash_is_rejected(tmp_path,missing):
    receipt=example(tmp_path)
    if missing:receipt['build_provenance']['inputs_sha256'].pop('template.yaml')
    else:receipt['build_provenance']['source_manifest_contract_sha256']='0'*64
    assert not inspect_receipt(tmp_path,receipt)[0]


def test_osworld_nonmodel_gui_skip_is_not_full_http_acceptance(tmp_path):
    source=tmp_path/'osworld';source.mkdir();receipt=example(source)
    (source/'e2e_test.py').write_text('original external desktop controller')
    receipt['http_acceptance']={'exit_code':0,'pass_count':6,'fail_count':0,'skip_count':1,'controller_sha256':hashlib.sha256((source/'e2e_test.py').read_bytes()).hexdigest()}
    assert not inspect_http_receipt(source,receipt)[0]
    receipt['build_provenance']['test_configuration']={'desktop_lifecycle_required':True}
    assert not inspect_http_receipt(source,receipt)[0]
    receipt['http_acceptance'].update(pass_count=18,skip_count=0)
    assert inspect_http_receipt(source,receipt)[0]


def test_cursor_installation_and_version_only_cannot_certify_native_api(tmp_path):
    source=tmp_path/'cursor-agent';source.mkdir();receipt=example(source)
    (source/'e2e_test.py').write_text('original Cursor native HTTP and SDK auth-refusal controller')
    receipt['http_acceptance']={'exit_code':0,'pass_count':10,'fail_count':0,'skip_count':0,'controller_sha256':hashlib.sha256((source/'e2e_test.py').read_bytes()).hexdigest()}
    assert not inspect_http_receipt(source,receipt)[0]
    receipt['build_provenance']['test_configuration']={'native_authentication_error_path_required':True,'synthetic_invalid_vendor_credential':True,'model_credentials_injected':False}
    assert not inspect_http_receipt(source,receipt)[0]
    receipt['http_acceptance']['pass_count']=16;assert inspect_http_receipt(source,receipt)[0]
    receipt['http_acceptance']['skip_count']=1;assert not inspect_http_receipt(source,receipt)[0]


def test_devin_installation_and_version_only_cannot_certify_native_api(tmp_path):
    source=tmp_path/'devin';source.mkdir();receipt=example(source)
    (source/'e2e_test.py').write_text('original Devin native HTTP and SDK auth-refusal controller')
    receipt['http_acceptance']={'exit_code':0,'pass_count':10,'fail_count':0,'skip_count':0,'controller_sha256':hashlib.sha256((source/'e2e_test.py').read_bytes()).hexdigest()}
    assert not inspect_http_receipt(source,receipt)[0]
    receipt['build_provenance']['test_configuration']={'native_authentication_error_path_required':True,'credential_absence_required':True,'model_credentials_injected':False}
    assert not inspect_http_receipt(source,receipt)[0]
    receipt['http_acceptance']['pass_count']=16;assert inspect_http_receipt(source,receipt)[0]
    receipt['http_acceptance']['skip_count']=1;assert not inspect_http_receipt(source,receipt)[0]
