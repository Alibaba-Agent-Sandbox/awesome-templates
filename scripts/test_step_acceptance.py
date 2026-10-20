"""Reject stale/misattributed acceptance even when its top-level pass is true."""
import hashlib

import pytest

from step_acceptance import inspect_receipt


def example(tmp_path):
    (tmp_path / "template.yaml").write_text("name: example\nversion: 1.0.0\nsmoke: [{command: hello}]\n")
    for name in ["Dockerfile", "commands.py", "requirements.lock"]:
        (tmp_path / name).write_text(name)
    return {"provider": "alicloud-express", "build_mode": "steps", "passed": True,
            "cleanup_verified": True, "template_version": "1.0.0",
            "commands": [{"name": "hello", "via": via, "ok": True} for via in ("cli", "sdk")],
            "build_provenance": {"inputs_sha256": {
                name: hashlib.sha256((tmp_path / name).read_bytes()).hexdigest()
                for name in ["Dockerfile", "commands.py", "requirements.lock"]}}}


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


def test_qualification_only_manifest_update_preserves_runtime_receipt(tmp_path):
    receipt = example(tmp_path)
    (tmp_path / "template.yaml").write_text("name: example\nversion: 1.0.0\nsmoke: [{command: hello}]\ntested_on: [alicloud-express]\n")
    assert inspect_receipt(tmp_path, receipt)[0]


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
