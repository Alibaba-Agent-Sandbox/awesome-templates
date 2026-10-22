"""Real subprocess regressions for full HTTP acceptance and fixture isolation."""
import json

import pytest

from template_http_acceptance import controller_environment, fixture_environment, run_controller


def controller(tmp_path, name, text):
    source = tmp_path / name
    source.mkdir()
    (source / "e2e_test.py").write_text(text)
    return source


def test_operator_credentials_cannot_reach_actual_controller(tmp_path, monkeypatch):
    for key in ["OPENAI_API_KEY", "ABX_SANDBOX_API_KEY", "CURSOR_API_KEY", "GH_TOKEN"]:
        monkeypatch.setenv(key, "synthetic-operator-secret")
    source = controller(tmp_path, "example", "import os\nassert not any(k in os.environ for k in ['OPENAI_API_KEY','ABX_SANDBOX_API_KEY','CURSOR_API_KEY','GH_TOKEN'])\nassert os.environ['E2E_RUN_LLM']=='0'\nprint('[PASS] credentials isolated')\n")
    proof = run_controller(source, {9000: "http://synthetic.invalid"}, tmp_path, {})
    assert proof["passed"] and proof["pass_count"] == 1


@pytest.mark.parametrize("name,output", [
    ("openclaw", "[PASS] health\n[SKIP] real gateway lifecycle"),
    ("osworld", "[PASS] version\n[SKIP] desktop"),
    ("cursor-agent", "[PASS] version\n[SKIP] authentication"),
    ("devin", "[PASS] version\n[SKIP] authentication"),
    ("chrome", "[PASS] version\n[SKIP] desktop"),
    ("example", ""),
    ("example", "[PASS] health\n[FAIL] actual operation"),
])
def test_zero_exit_does_not_hide_missing_or_failed_operations(tmp_path, name, output):
    source = controller(tmp_path, name, "print(" + repr(output) + ")\n")
    _, fixture, _ = fixture_environment(name)
    urls = {port: "http://synthetic.invalid" for port in [9000, 9222, 6080]}
    assert run_controller(source, urls, tmp_path, fixture)["passed"] is False


def test_gateway_token_is_shared_only_with_owned_servers_and_not_evidence():
    server, controller_env, proof = fixture_environment("openclaw")
    token = server["OPENCLAW_GATEWAY_TOKEN"]
    assert controller_env["OPENCLAW_GATEWAY_TOKEN"] == token
    assert len(token) >= 40 and token not in json.dumps(proof)
    assert proof["gateway_lifecycle_required"]


def test_unrelated_secret_cannot_be_forwarded_as_a_fixture(tmp_path):
    with pytest.raises(ValueError, match="only owned"):
        controller_environment(tmp_path, {9000: "http://synthetic.invalid"},
                               {"OPENAI_API_KEY": "synthetic-secret"})
