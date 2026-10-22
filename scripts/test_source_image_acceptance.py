"""Qualification guards reject changed source, skipped work and uncertain cleanup."""
import copy
import hashlib
import json

import pytest

import source_image_acceptance as audit


def native_fixture(tmp_path):
    source = tmp_path / "native-example"
    source.mkdir()
    (source / "template.yaml").write_text("name: native-example\nversion: '1.0.0'\nresources: {cpu: 2, memory: 2048}\n")
    (source / "Dockerfile").write_text("FROM python:3.13-slim\nCOPY commands.py /home/user/app/commands.py\n")
    (source / "commands.py").write_text("# public runtime\n")
    (source / "e2e_test.py").write_text("print('[PASS] actual API')\n")
    (tmp_path / "scripts").mkdir()
    controller = tmp_path / "scripts/opensandbox_template_e2e.py"
    controller.write_text("# immutable test controller\n")
    receipt = {"provider": "opensandbox", "build_mode": "image", "template": source.name,
        "template_version": "1.0.0", "verification_type": "source-image-native-opensandbox-docker-http",
        "passed": True, "cleanup_verified": True, "pins": copy.deepcopy(audit.PINS),
        "workflow_job_conclusion": "success", "test_configuration": {"model_credentials_injected": False},
        "workflow_run_id": 123, "source_commit": "a" * 40,
        "context_sha256": audit.context_sha256(source), "server_sdk_commit": audit.server_commit(source),
        "controller_sha256": hashlib.sha256(controller.read_bytes()).hexdigest(),
        "images": {"template_image_id": "sha256:" + "b" * 64},
        "cleanup_observations": {"sdk_not_found": True, "owned_docker_containers_absent": True, "errors": []},
        "execution_identity": {"uid": 1000, "probe_exit_code": 0},
        "http_acceptance": {"passed": True, "exit_code": 0, "pass_count": 3, "fail_count": 0,
            "skip_count": 0, "verifier_sha256": hashlib.sha256((source / "e2e_test.py").read_bytes()).hexdigest()},
        "checks": ["independent Docker identity matches exact built image", "actual runtime command bytes match source",
            "SDK real shell Python program", "SDK file write/read", "SDK file removal readback",
            "complete current external HTTP controller", "independent SDK and Docker absence",
            "owned provider engine stopped and reaped", "owned original server process stopped"]}
    return source, receipt


@pytest.mark.parametrize("field,value", [
    ("cleanup_observations.sdk_not_found", False),
    ("cleanup_observations.owned_docker_containers_absent", False),
    ("cleanup_observations.errors", ["unresolved"]),
    ("execution_identity.uid", 0),
    ("execution_identity.uid", True),
    ("execution_identity.probe_exit_code", 1),
    ("http_acceptance.passed", False),
    ("http_acceptance.fail_count", 1),
    ("http_acceptance.pass_count", 0),
    ("http_acceptance.pass_count", True),
    ("http_acceptance.verifier_sha256", "0" * 64),
    ("test_configuration.model_credentials_injected", True),
    ("workflow_job_conclusion", "failure"),
    ("controller_sha256", "0" * 64),
    ("source_commit", "main"),
    ("server_sdk_commit", "0" * 40),
    ("images.template_image_id", "mutable:tag"),
])
def test_native_pass_cannot_survive_missing_prerequisites(tmp_path, field, value):
    source, receipt = native_fixture(tmp_path)
    assert audit.inspect_opensandbox(source, receipt, tmp_path)
    target = receipt
    parts = field.split(".")
    for part in parts[:-1]:
        target = target[part]
    target[parts[-1]] = value
    assert not audit.inspect_opensandbox(source, receipt, tmp_path)


def test_changed_runtime_or_controller_invalidates_native_receipt(tmp_path):
    source, receipt = native_fixture(tmp_path)
    assert audit.inspect_opensandbox(source, receipt, tmp_path)
    (source / "commands.py").write_text("# changed runtime\n")
    assert not audit.inspect_opensandbox(source, receipt, tmp_path)


def test_a_managed_interpreter_receipt_cannot_qualify_a_source_template(tmp_path):
    source, receipt = native_fixture(tmp_path)
    receipt.update(template="opensandbox-code-interpreter", verification_type="native-opensandbox-docker-sdk-and-interpreter")
    assert not audit.inspect_opensandbox(source, receipt, tmp_path)
