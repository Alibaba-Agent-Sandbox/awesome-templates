"""Gateway verifier failures must stay red and never skip independent cleanup."""
from __future__ import annotations

import importlib.util
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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


SOURCE = Path(__file__).parent / "scripts/smoke.py"
FIELDS = {"schemaVersion", "status", "phase", "code", "cleanup_attempted", "cleanup_confirmed",
          "http_status", "terminal_status"}


@pytest.fixture
def report_root(tmp_path, monkeypatch):
    monkeypatch.setattr(smoke, "__file__", str(tmp_path / "scripts/smoke.py"))
    return tmp_path


def latest(root):
    return json.loads((root / ".abx/agents-smoke-reports/latest.json").read_text())


@pytest.mark.parametrize("failure,code", [
    (smoke.SmokeFailure("agent_turn_completed"), "agent_turn_completed"),
    (httpx.ConnectError("test-secret-url-and-credential"), "gateway_transport"),
    (RuntimeError("test-secret-url-and-credential"), "unexpected_error"),
    (smoke.SmokeFailure("test-secret-url-and-credential"), "unexpected_error"),
])
def test_failed_main_preserves_safe_phase_after_hook_directory_deleted(report_root, monkeypatch, capsys, failure, code):
    hook = report_root / ".abx/hook-test"
    hook.mkdir(parents=True)
    context, result = hook / "context.json", hook / "result.json"
    context.write_text(json.dumps({"hookId": "test-private-hook-id", "operationId": "test-private-operation-id"}))
    monkeypatch.setenv("ABX_HOOK_CONTEXT_FILE", str(context))
    monkeypatch.setenv("ABX_HOOK_RESULT_FILE", str(result))
    monkeypatch.setattr(sys, "argv", ["smoke.py"])
    failure.terminal_status = "failed"
    def run(*args, report, **kwargs):
        assert latest(report_root)["status"] == "running"  # Before the first business request.
        report.step("summary_turn")
        report.cleanup(True)
        raise failure
    monkeypatch.setattr(smoke, "run", run)
    assert smoke.main() == 1
    assert json.loads(result.read_text())["status"] == "failed"
    shutil.rmtree(hook)  # Existing CLI runHooks finally behavior.
    value = latest(report_root)
    assert value["status"] == "failed" and value["phase"] == "summary_turn" and value["code"] == code
    assert value["cleanup_confirmed"] is True and set(value) <= FIELDS
    data = "".join(p.read_text() for p in (report_root / ".abx/agents-smoke-reports").glob("*"))
    assert all(word not in data + capsys.readouterr().out for word in
               ["test-secret-url-and-credential", "test-private-hook-id", "test-private-operation-id"])
    assert ("terminal_status" in value) is (type(failure) is smoke.SmokeFailure)


def test_success_and_fresh_history_do_not_replace_prior_report(report_root, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["smoke.py"])
    def run(*args, report, **kwargs):
        report.step("share_results")
        report.cleanup(True)
    monkeypatch.setattr(smoke, "run", run)
    assert smoke.main() == 0
    directory = report_root / ".abx/agents-smoke-reports"
    old = {p.name: p.read_bytes() for p in directory.glob("*.jsonl")}
    assert latest(report_root)["status"] == "passed"
    assert smoke.main() == 0
    assert len(list(directory.glob("*.jsonl"))) == 2
    assert all((directory / name).read_bytes() == raw for name, raw in old.items())


def test_unknown_terminal_or_http_data_is_not_serialized(report_root):
    report = smoke.SmokeReport()
    try:
        error = smoke.SmokeFailure("agent_turn_completed")
        error.http_status, error.terminal_status = "test-secret", ["test-secret"]
        report.failed(error)
        value = latest(report_root)
        assert "http_status" not in value and "terminal_status" not in value and set(value) <= FIELDS
    finally:
        report.close()


def test_atomic_latest_io_failure_never_returns_success(report_root, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["smoke.py"])
    called = []
    monkeypatch.setattr(smoke, "run", lambda *args, **kwargs: called.append(True))
    monkeypatch.setattr(smoke.os, "replace", lambda *args: (_ for _ in ()).throw(OSError("test-private-path")))
    assert smoke.main() == 1 and called == []


def test_report_limits_and_symlink_parent_fail_before_business(report_root, monkeypatch):
    report = smoke.SmokeReport()
    try:
        report.MAX_ROWS = 1
        with pytest.raises(OSError): report.step("health")
        assert latest(report_root)["status"] == "running"
    finally:
        report.close()
    shutil.rmtree(report_root / ".abx")
    outside = report_root / "outside"
    outside.mkdir()
    (report_root / ".abx").symlink_to(outside, target_is_directory=True)
    with pytest.raises(OSError): smoke.SmokeReport()
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize("failing_phase", ["summary_turn", "cleanup"])
def test_progress_write_failure_after_upload_still_attempts_cleanup(report_root, monkeypatch, failing_phase):
    payload = {"/healthz": {"protocol": "agent-sandbox-managed-agents/v1"},
               "/v1/agent-sandbox/capabilities": {"protocol": "agent-sandbox-managed-agents/v1"},
               "/v1/models": {"data": [{"id": "model"}]}, "/v1/files": {"id": "test-input"},
               "/v1/agents/sessions": {"id": "test-session"}}
    monkeypatch.setattr(smoke, "request", lambda client, method, path, expected, **kwargs:
        httpx.Response(expected, json=payload.get(path, {}), headers={"X-Agent-Sandbox-Submission-Id": "test-submission"}))
    monkeypatch.setattr(smoke, "wait_submission", lambda *args: {"turn_id": "test-first"})
    monkeypatch.setattr(smoke, "submit", lambda *args: {"turn_id": "test-second"})
    monkeypatch.setattr(smoke, "artifact", lambda client, sid, turn, name: (turn + name).encode())
    monkeypatch.setattr(smoke, "verify_csv", lambda *args: None)
    monkeypatch.setattr(smoke, "close", lambda *args: None)
    calls = []
    monkeypatch.setattr(smoke, "cleanup", lambda *args: calls.append(args) or True)
    class Report:
        def step(self, phase):
            if phase == failing_phase: raise smoke.SmokeFailure("report_io")
        def cleanup(self, confirmed): assert confirmed is True
    with pytest.raises(smoke.SmokeFailure, match="report_io"):
        smoke.run("https://gateway.invalid", "test-token", None, 10, report=Report())
    assert len(calls) == 1


def copy_script(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    shutil.copy2(SOURCE, scripts / "smoke.py")
    shutil.copytree(SOURCE.parents[1] / "fixtures", tmp_path / "fixtures")
    return scripts / "smoke.py"


def test_real_local_http_error_records_only_actual_status_before_first_request(tmp_path):
    script = copy_script(tmp_path)
    observed = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_GET(self):
            observed.append(latest(tmp_path))
            self.send_response(503); self.end_headers(); self.wfile.write(b"test-secret-model-response")
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        result = subprocess.run([sys.executable, str(script), "--base-url", f"http://127.0.0.1:{server.server_port}"],
            env={**os.environ, "AGENTS_API_KEY": "test-secret-business-key"}, capture_output=True, text=True, timeout=10)
        value = latest(tmp_path)
        assert result.returncode == 1 and observed[0]["status"] == "running" and observed[0]["phase"] == "health"
        assert value["code"] == "http_200" and value["http_status"] == 503 and value["phase"] == "health"
        assert "test-secret" not in json.dumps(value) + result.stdout + result.stderr
    finally:
        server.shutdown(); server.server_close(); thread.join(5)
    assert not thread.is_alive()


def test_sigkill_retains_last_running_phase_without_http_or_model(tmp_path):
    script = copy_script(tmp_path)
    code = ("import importlib.util,time; s=importlib.util.spec_from_file_location('owned_report'," + repr(str(script)) + ");"
            "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);r=m.SmokeReport();r.step('summary_turn');time.sleep(30)")
    child = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                if latest(tmp_path)["phase"] == "summary_turn": break
            except FileNotFoundError: pass
            time.sleep(0.02)
        else: pytest.fail("owned reporter did not persist its running phase")
        child.kill(); child.wait(timeout=5)
        value = latest(tmp_path)
        assert value["status"] == "running" and value["phase"] == "summary_turn"
        assert all(json.loads(line)["status"] != "passed" for p in (tmp_path / ".abx/agents-smoke-reports").glob("*.jsonl") for line in p.read_text().splitlines())
    finally:
        if child.poll() is None: child.kill(); child.wait(timeout=5)
        child.stderr.close()


def test_report_close_failure_is_nonzero_without_raw_error(report_root, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["smoke.py"])
    monkeypatch.setattr(smoke, "run", lambda *args, report, **kwargs: report.cleanup(True))
    original_close = smoke.SmokeReport.close
    def close(self):
        original_close(self)
        raise OSError("test-secret-close-detail")
    monkeypatch.setattr(smoke.SmokeReport, "close", close)
    assert smoke.main() == 1
    output = capsys.readouterr()
    assert "test-secret-close-detail" not in output.out + output.err and "PASS:" not in output.out
    assert "report_io" in output.out
