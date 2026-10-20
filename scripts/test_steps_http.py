"""Exercise real controller subprocess results and credential isolation."""
from types import SimpleNamespace
from unittest.mock import patch

import pytest

import express_e2e
from run_steps_e2e import configure_http_fixture, http_callback
from prepare_steps import ROOT, prepare
import hashlib
import json
import yaml


@pytest.mark.parametrize("exit_code,outcome", [(0, "PASS"), (1, "FAIL")])
def test_controller_runs_once_and_failed_assertions_cannot_pass(tmp_path, monkeypatch, exit_code, outcome):
    monkeypatch.setenv("ABX_SANDBOX_API_KEY", "synthetic-controller-secret")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-model-secret")
    (tmp_path / "template.yaml").write_text("ports: [9000]\n")
    (tmp_path / "e2e_test.py").write_text(
        "import os\n"
        "assert 'ABX_SANDBOX_API_KEY' not in os.environ\n"
        "assert 'OPENAI_API_KEY' not in os.environ\n"
        "assert os.environ['E2E_BASE_URL'] == 'http://synthetic.invalid'\n"
        "assert os.environ['E2E_RUN_LLM'] == '0'\n"
        f"print('[{outcome}] actual-controller-result')\nraise SystemExit({exit_code})\n")

    class Sandbox:
        network = SimpleNamespace(get_url=lambda port: "http://synthetic.invalid")

        async def close(self):
            pass

        @classmethod
        async def connect(cls, sandbox_id):
            return cls()

    report = {}
    with patch("agent_sandbox.api.sandbox.Sandbox", Sandbox), patch.object(express_e2e, "default_sdk", return_value="smoke"):
        callback = http_callback(tmp_path, tmp_path, report)
        if exit_code:
            with pytest.raises(RuntimeError, match="controller failed"):
                callback("synthetic", "hello", {})
            assert report["http_acceptance"]["fail_count"] == 1
        else:
            assert callback("synthetic", "hello", {}) == "smoke"
            (tmp_path / "e2e_test.py").write_text("raise RuntimeError('must never run twice')")
            assert callback("synthetic", "hello", {}) == "smoke"
            assert report["http_acceptance"]["pass_count"] == 1
        assert report["http_acceptance"]["exit_code"] == exit_code


def test_gateway_fixture_is_generated_after_installers_and_absent_from_public_proof():
    manifest, proof = prepare(ROOT / "openclaw")
    original = list(manifest["build"]["steps"])
    env = configure_http_fixture(ROOT / "openclaw", manifest, proof)
    steps = manifest["build"]["steps"]
    assert steps[:-2] + [steps[-1]] == original
    assert steps[-2] == {"type": "ENV", "args": ["OPENCLAW_GATEWAY_TOKEN", env["OPENCLAW_GATEWAY_TOKEN"]]}
    assert steps[-1] == {"type": "USER", "args": ["user"]}
    assert len(env["OPENCLAW_GATEWAY_TOKEN"]) >= 40
    assert env["OPENCLAW_GATEWAY_TOKEN"] not in json.dumps(proof)
    assert proof["test_configuration"]["model_credentials_injected"] is False
    assert proof["generated_manifest_sha256"] == hashlib.sha256(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True).encode()).hexdigest()
    assert proof["steps_json_bytes"] <= 15000


def test_controller_fixture_cannot_forward_an_operator_credential(tmp_path):
    with pytest.raises(ValueError, match="only the generated owned gateway fixture"):
        http_callback(tmp_path, tmp_path, {}, {"OPENAI_API_KEY": "synthetic-operator-secret"})


def test_osworld_requires_real_desktop_and_rejects_nonmodel_skip(tmp_path):
    source=tmp_path/'osworld';source.mkdir();(source/'template.yaml').write_text('ports: [9000]\n')
    (source/'e2e_test.py').write_text("import os\nassert os.environ['E2E_REQUIRE_DESKTOP']=='1'\nassert os.environ['E2E_RUN_DESKTOP']=='1'\nprint('[PASS] basic HTTP')\nprint('[SKIP] GUI task')\n")
    proof={};manifest={'build':{'steps':[]}}
    assert configure_http_fixture(source,manifest,proof)=={}
    assert proof['test_configuration']['desktop_lifecycle_required'] is True
    class Sandbox:
        network=SimpleNamespace(get_url=lambda port:'http://synthetic.invalid')
        async def close(self):pass
        @classmethod
        async def connect(cls,sandbox_id):return cls()
    report={}
    with patch('agent_sandbox.api.sandbox.Sandbox',Sandbox),patch.object(express_e2e,'default_sdk',return_value='smoke'):
        callback=http_callback(source,tmp_path,report)
        with pytest.raises(RuntimeError,match='desktop lifecycle'):callback('synthetic','desktop',{})
    assert report['http_acceptance']['skip_count']==1


def test_chrome_controller_receives_all_native_ports_and_requires_gui(tmp_path):
    source=tmp_path/'chrome';source.mkdir()
    (source/'template.yaml').write_text('ports: [9000,9222,6080]\n')
    (source/'e2e_test.py').write_text("import os\nassert os.environ['E2E_CHROME_CDP_URL']=='http://synthetic.invalid/9222'\nassert os.environ['E2E_CHROME_VNC_URL']=='http://synthetic.invalid/6080'\nassert os.environ['E2E_REQUIRE_CHROME']=='1'\nassert os.environ['E2E_WORKSPACE']=='/home/user/workspace'\nprint('[PASS] native controller inputs')\n")
    class Sandbox:
        network=SimpleNamespace(get_url=lambda port:'http://synthetic.invalid/'+str(port))
        async def close(self):pass
        @classmethod
        async def connect(cls,sandbox_id):return cls()
    report={}
    with patch('agent_sandbox.api.sandbox.Sandbox',Sandbox),patch.object(express_e2e,'default_sdk',return_value='smoke'):
        assert http_callback(source,tmp_path,report)('synthetic','chrome_smoke',{})=='smoke'
    assert report['http_acceptance']['pass_count']==1
