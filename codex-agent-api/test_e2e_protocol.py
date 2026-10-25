"""Acceptance-harness regression with fake remote responses and real test processes.

These tests do not count as a real Codex/model/provider pass.
"""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import shutil
import subprocess

import httpx
import pytest

SPEC = importlib.util.spec_from_file_location("codex_api_e2e_protocol", Path(__file__).with_name("e2e_test.py"))
e2e = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(e2e)
FIXED_SOURCE = '''def normalize_usernames(values):
    result = []
    for value in values:
        value = value.strip().lower()
        if value and value not in result:
            result.append(value)
    return result
'''


@pytest.mark.parametrize("behavior", ["fix", "marker_only", "wrong_report", "wrong_resume", "forged_test_output"])
def test_fake_remote_coding_acceptance_rejects_false_success(monkeypatch, tmp_path, behavior):
    monkeypatch.setenv("E2E_REQUIRE_LLM", "1")
    monkeypatch.delenv("E2E_RUN_LLM", raising=False)
    monkeypatch.setattr(e2e, "WORKSPACE", str(tmp_path))
    checks = []
    calls = []
    task = None
    shell_runs = []

    def check(name, ok):
        checks.append((name, bool(ok)))

    def handler(request):
        nonlocal task
        path = request.url.path
        calls.append((request.method, path))
        payload = json.loads(request.content) if request.content else {}
        if request.method == "POST" and path == "/files/upload-stream":
            target = Path(payload["path"])
            assert tmp_path in target.parents and target.name == "normalizer.py"
            task = target.parent
            task.mkdir()
            target.write_bytes(base64.b64decode(payload["content_base64"]))
            assert not list(task.glob("test*"))
            return httpx.Response(200, json={"bytes": target.stat().st_size})
        if request.method == "POST" and path == "/shell":
            assert payload["cwd"] == str(task)
            argv = shlex.split(payload["command"])
            assert argv[:5] == ["env", "-i", "PATH=/usr/local/bin:/usr/bin:/bin", "python3", "-I"]
            assert argv[6].startswith(e2e.FIXED_TESTS)  # Fixed assertions plus a fresh post-return completion ACK.
            assert not list(task.glob("test*"))  # Tests are never exposed as model-editable files.
            result = subprocess.run(argv, cwd=task, capture_output=True, text=True, timeout=10)
            shell_runs.append(result.returncode)
            return httpx.Response(200, json={"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        if request.method == "POST" and path == "/v1/agents/sessions":
            assert payload["background"] is True
            assert "Fix the EXISTING normalizer.py" in payload["input"]
            assert "Do not create or edit any test files" in payload["input"]
            assert (task / "normalizer.py").read_text() == e2e.BUGGY_SOURCE
            if behavior != "marker_only":
                (task / "normalizer.py").write_text(FIXED_SOURCE)
            if behavior == "forged_test_output":
                (task / "normalizer.py").write_text("import sys,os\nsys.stderr.write('Ran 6 tests in 0.0s\\n\\nOK\\n');sys.stderr.flush();os._exit(0)\n")
            report = {"input": e2e.REPORT_INPUT, "output": [] if behavior == "wrong_report" else e2e.REPORT_OUTPUT}
            (task / "normalization-report.json").write_text(json.dumps(report))
            return httpx.Response(200, json={"id": "sess_fixture", "status": "in_progress"})
        if request.method == "GET" and path == "/v1/agents/sessions/sess_fixture":
            return httpx.Response(200, json={"id": "sess_fixture", "status": "idle"})
        if request.method == "GET" and path.endswith("/items"):
            return httpx.Response(200, json={"data": [
                {"type": "item.completed", "item": {"type": "command_execution", "status": "completed", "exit_code": 0}},
                {"type": "item.completed", "item": {"type": "agent_message", "text": "ABX_E2E_OK"}},
            ]})
        if request.method == "GET" and path == "/files/download-stream":
            target = Path(request.url.params["path"])
            assert target.parent == task
            return httpx.Response(200, json={"content_base64": base64.b64encode(target.read_bytes()).decode()})
        if request.method == "POST" and path.endswith("/events"):
            assert payload["stream"] is True and "Continue the same task" in payload["input"]
            report_bytes = (task / "normalization-report.json").read_bytes()
            summary = {"report_sha256": "wrong" if behavior == "wrong_resume" else hashlib.sha256(report_bytes).hexdigest(),
                       "normalized_count": len(e2e.REPORT_OUTPUT)}
            (task / "resume-summary.json").write_text(json.dumps(summary))
            text = "event: agent.session.output_item.done\ndata: " + json.dumps({"type": "agent.session.output_item.done", "item": {"type": "agent_message", "text": "ABX_RESUME_OK"}}) + "\n\n"
            text += "event: agent.session.turn.completed\ndata: " + json.dumps({"type": "agent.session.turn.completed"}) + "\n\n"
            return httpx.Response(200, text=text, headers={"content-type": "text/event-stream"})
        if request.method == "GET" and "/artifacts/" in path:
            identifier = path.rsplit("/", 1)[1]
            relative = base64.urlsafe_b64decode(identifier + "=" * (-len(identifier) % 4)).decode()
            target = tmp_path / relative
            assert target.parent == task
            return httpx.Response(200, json={"content": target.read_text()})
        if request.method == "DELETE" and path == "/v1/agents/sessions/sess_fixture":
            return httpx.Response(200, json={"deleted": True})
        if request.method == "DELETE" and path == "/files":
            assert request.url.params["path"] == str(task)
            shutil.rmtree(task)
            return httpx.Response(200, json={"deleted": True})
        raise AssertionError(f"Unexpected fixture protocol: {request.method} {path}")

    with httpx.Client(base_url="https://fake-remote.invalid", transport=httpx.MockTransport(handler)) as client:
        e2e._coding_acceptance(client, check)
    passed = {name for name, ok in checks if ok}
    failed = {name for name, ok in checks if not ok}
    assert shell_runs[0] == 1
    assert "L3 existing source reproduces fixed-test failures" in passed
    assert "L3 owned coding project cleanup" in passed
    assert not task.exists()
    if behavior == "fix":
        assert not failed
        assert shell_runs == [1, 0, 0]
        assert "L3 independently verified resume artifact" in passed
    elif behavior == "marker_only":
        assert "L3 existing source changed on target" in failed
        assert "L3 controller-owned fixed tests pass on target" in failed
    elif behavior == "forged_test_output":
        assert "L3 controller-owned fixed tests pass on target" in failed
    elif behavior == "wrong_report":
        assert "L3 independent new report contents" in failed
    elif behavior == "wrong_resume":
        assert "L3 independently verified resume artifact" in failed


def test_require_llm_cannot_skip(monkeypatch):
    monkeypatch.setenv("E2E_REQUIRE_LLM", "1")
    monkeypatch.setenv("E2E_RUN_LLM", "0")
    checks = []
    with httpx.Client(transport=httpx.MockTransport(lambda request: pytest.fail("No remote request expected"))) as client:
        e2e._coding_acceptance(client, lambda name, ok: checks.append((name, ok)))
    assert checks == [("L3 real coding task required", False)]


def test_application_bearer_and_provider_gateway_headers_are_separate(monkeypatch):
    monkeypatch.setenv("ABX_SERVER_TOKEN", "synthetic-app-token")
    monkeypatch.setenv("E2E_TOKEN", "retired-token-must-not-be-used")
    monkeypatch.setenv("E2E_SERVER_TOKEN", "retired-server-token-must-not-be-used")
    monkeypatch.setattr(e2e, "_GATEWAY_HEADERS", {"X-Access-Token": "synthetic-gateway-token"})
    assert e2e._headers() == {"Authorization": "Bearer synthetic-app-token", "X-Access-Token": "synthetic-gateway-token"}
