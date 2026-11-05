"""Gateway verifier failures must stay red and never skip independent cleanup."""
from __future__ import annotations

import importlib.util
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
    smoke.verify_csv(b"month,total\n2026-01,30\n2026-02,7\n", False)
    for content in (b"month,total\n2026-01,37\n", b"month,total,share\n2026-01,30,nan\n2026-02,7,nan\n"):
        with pytest.raises(smoke.SmokeFailure):
            smoke.verify_csv(content, b"share" in content)


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
    monkeypatch.setattr(smoke, "artifact", lambda *args: b"captured")
    with pytest.raises(smoke.SmokeFailure, match="original_business_failure" if primary_failure else "owned_cleanup_incomplete"):
        smoke.run("https://gateway.invalid", "test-token", None, 10)
