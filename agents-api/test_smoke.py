"""Gateway verifier failures must stay red and never skip independent cleanup."""
from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

SPEC = importlib.util.spec_from_file_location("managed_template_smoke", Path(__file__).parent / "scripts/smoke.py")
smoke = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(smoke)


def test_close_failure_still_attempts_session_and_input_deletion():
    calls = []
    def request(client, method, path, expected, **kwargs):
        calls.append(path)
        if "/sessions/" in path:
            raise smoke.SmokeFailure("http_200")  # Active delete409 must remain a failure.
    with patch.object(smoke, "close", side_effect=smoke.SmokeFailure("cleanup_deadline")) as close, patch.object(smoke, "request", side_effect=request):
        assert not smoke.cleanup(object(), "session", False, "input", 1)
    close.assert_called_once()
    assert calls == ["/v1/agents/sessions/session", "/v1/files/input"]


def test_successfully_released_compute_is_not_closed_again():
    with patch.object(smoke, "close") as close, patch.object(smoke, "request") as request:
        assert smoke.cleanup(object(), "session", True, "input", 1)
    close.assert_not_called()
    assert [call.args[2] for call in request.call_args_list] == ["/v1/agents/sessions/session", "/v1/files/input"]


def test_independent_csv_rejects_wrong_results_and_non_finite_share():
    smoke.verify_csv(b"month,total\n2026-01,30.00\n2026-02,10.00\n", False)
    smoke.verify_csv(b"month,total,share\n2026-01,30.00,0.750000\n2026-02,10.00,0.250000\n", True)
    for content in (b"month,total\n2026-01,37\n", b"month,total,share\n2026-01,30,nan\n2026-02,10,nan\n"):
        with pytest.raises(smoke.SmokeFailure):
            smoke.verify_csv(content, b"share" in content)


def test_seed_program_fails_the_unchanged_original_tests(tmp_path):
    """The model task starts with a real source defect, not an already-green sample."""
    shutil.copytree(smoke.FIXTURES, tmp_path / "exercise")
    result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                            cwd=tmp_path / "exercise", capture_output=True, text=True, timeout=20)
    assert result.returncode != 0
    assert "FAILED (failures=2)" in result.stderr


def test_trusted_inspection_finishes_before_continuation_and_close(monkeypatch):
    order = []
    payload = {"/healthz": {"protocol": "agent-sandbox-managed-agents/v1"},
               "/v1/agent-sandbox/capabilities": {"protocol": "agent-sandbox-managed-agents/v1"},
               "/v1/models": {"data": [{"id": "model"}]}, "/v1/files": {"id": "input"},
               "/v1/agents/sessions": {"id": "session"}}
    def request(client, method, path, expected, **kwargs):
        if method == "POST" and path == "/v1/agents/sessions":
            assert kwargs["json"]["x_agent_sandbox"]["input_files"] == [
                {"file_id": "input", "path": "/workspace/input/sales.csv"}]
            assert "/workspace/input/sales.csv" in kwargs["json"]["input"]
        return httpx.Response(expected, json=payload.get(path, {}),
                              headers={"X-Agent-Sandbox-Submission-Id": "submission"})
    monkeypatch.setattr(smoke, "request", request)
    monkeypatch.setattr(smoke, "wait_submission", lambda *args: {"turn_id": "first"})
    def submit(*args):
        assert "/workspace/input/sales.csv" in args[2]
        order.append("submit_second")
        return {"turn_id": "second"}
    monkeypatch.setattr(smoke, "submit", submit)
    monkeypatch.setattr(smoke, "artifact", lambda client, sid, turn, name: (turn + name).encode())
    monkeypatch.setattr(smoke, "verify_csv", lambda *args: None)
    monkeypatch.setattr(smoke, "close", lambda *args: order.append("close"))
    monkeypatch.setattr(smoke, "cleanup", lambda *args: True)
    def inspect(stage, sid, turn, artifacts):
        assert sid == "session" and artifacts["aggregate.py"] == (turn + "aggregate.py").encode()
        order.append("inspect_" + stage)
    smoke.run("https://gateway.invalid", "test-token", None, 10, inspect_turn=inspect)
    assert order == ["inspect_summary", "submit_second", "inspect_share", "close"]


@pytest.mark.parametrize("primary_failure", [False, True])
def test_cleanup_failure_never_turns_business_success_green_or_masks_primary(primary_failure, monkeypatch):
    def request(client, method, path, expected, **kwargs):
        payload = {"/healthz": {"protocol": "agent-sandbox-managed-agents/v1"},
                   "/v1/agent-sandbox/capabilities": {"protocol": "agent-sandbox-managed-agents/v1"},
                   "/v1/models": {"data": [{"id": "model"}]}, "/v1/files": {"id": "input"},
                   "/v1/agents/sessions": {"id": "session"}}
        return httpx.Response(expected, json=payload.get(path, {}), headers={"X-Agent-Sandbox-Submission-Id": "submission"})
    monkeypatch.setattr(smoke, "request", request)
    monkeypatch.setattr(smoke, "cleanup", lambda *args: False)
    monkeypatch.setattr(smoke, "close", lambda *args: None)
    monkeypatch.setattr(smoke, "submit", lambda *args: {"turn_id": "second"})
    def wait(*args):
        if primary_failure:
            raise smoke.SmokeFailure("original_business_failure")
        return {"turn_id": "first"}
    monkeypatch.setattr(smoke, "wait_submission", wait)
    monkeypatch.setattr(smoke, "verify_csv", lambda *args: None)
    monkeypatch.setattr(smoke, "artifact", lambda client, sid, turn, name: (turn + name).encode())
    with pytest.raises(smoke.SmokeFailure, match="original_business_failure" if primary_failure else "owned_cleanup_incomplete"):
        smoke.run("https://gateway.invalid", "test-token", None, 10)
