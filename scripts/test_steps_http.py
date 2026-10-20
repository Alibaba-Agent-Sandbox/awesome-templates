"""Exercise real controller subprocess results and credential isolation."""
from types import SimpleNamespace
from unittest.mock import patch

import pytest

import express_e2e
from run_steps_e2e import http_callback


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
