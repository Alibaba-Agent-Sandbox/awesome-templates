"""Protocol regressions with a fake remote agent and actual local test subprocesses.

These tests verify the acceptance harness; they are not model/provider evidence.
"""
from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess

import httpx
import pytest

SPEC = importlib.util.spec_from_file_location("opencode_e2e_protocol", Path(__file__).with_name("e2e_test.py"))
e2e = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(e2e)


@pytest.mark.parametrize("agent_behavior", ["fix", "marker_only", "tamper_tests"])
def test_remote_coding_protocol_detects_real_fix_and_rejects_false_success(monkeypatch, tmp_path, agent_behavior):
    monkeypatch.setattr(e2e, "WORKSPACE", str(tmp_path))
    monkeypatch.setattr(e2e, "RUN_LLM", "1")
    monkeypatch.setattr(e2e, "REQUIRE", True)
    monkeypatch.setattr(e2e, "RESULTS", [])
    calls = []
    model_calls = []
    seeded_project = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seeded_project
        assert request.url.host == "remote-target.invalid"
        calls.append((request.method, request.url.path))
        payload = json.loads(request.content) if request.content else {}
        if request.url.path == "/files/upload-stream" and request.method == "POST":
            path = Path(payload["path"])
            assert tmp_path in path.parents
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(base64.b64decode(payload["content_base64"]))
            seeded_project = path.parent
            return httpx.Response(200, json={"success": True})
        if request.url.path == "/shell" and request.method == "POST":
            assert payload["cwd"] == str(seeded_project)
            # Follow the real /shell protocol: argv, not sh -c or shell operators.
            argv = shlex.split(payload["command"])
            assert "&&" not in argv and "cd" not in argv
            completed = subprocess.run(argv, cwd=seeded_project, capture_output=True,
                                       text=True, timeout=10, env={"PATH": "/usr/local/bin:/usr/bin:/bin"})
            return httpx.Response(200, json={"exit_code": completed.returncode,
                "stdout": completed.stdout, "stderr": completed.stderr})
        if request.url.path == "/commands/opencode_run" and request.method == "POST":
            assert set(payload) == {"prompt", "cwd"}
            assert payload["cwd"] == str(seeded_project)
            assert (seeded_project / "calc.py").read_text() == "def add(a, b):\n    return a - b\n"
            assert "Do not modify test_calc.py" in payload["prompt"]
            model_calls.append(payload)
            marker = re.search(r"ABX_E2E_[0-9a-f]+", payload["prompt"]).group()
            if agent_behavior == "fix":
                (seeded_project / "calc.py").write_text("def add(a, b):\n    return (a + b)\n")
            elif agent_behavior == "tamper_tests":
                (seeded_project / "test_calc.py").write_text("# agent deleted the failing tests\n")
            (seeded_project / "report.txt").write_text("Changed addition; simulated agent report.\n")
            (seeded_project / "acceptance.txt").write_text(marker + "\n")
            return httpx.Response(200, json={"result": {"text": marker, "session_id": "ses_fake_protocol_only"}})
        if request.url.path == "/files/download-stream" and request.method == "GET":
            path = Path(request.url.params["path"])
            assert path.parent == seeded_project
            return httpx.Response(200, json={"content_base64": base64.b64encode(path.read_bytes()).decode()})
        if request.url.path == "/files" and request.method == "DELETE":
            assert request.url.params["path"] == str(seeded_project)
            shutil.rmtree(seeded_project)
            return httpx.Response(200, json={"success": True})
        raise AssertionError("Unexpected HTTP protocol operation")

    with httpx.Client(base_url="https://remote-target.invalid", transport=httpx.MockTransport(handler)) as client:
        e2e.check_model_call(client)
    assert len(model_calls) == 1
    assert not seeded_project.exists()
    passed = {name for status, name in e2e.RESULTS if status == "PASS"}
    failed = {name for status, name in e2e.RESULTS if status == "FAIL"}
    assert "L3 seeded existing source reproduces failing independent tests" in passed
    assert "L3 owned coding project cleanup" in passed
    if agent_behavior == "fix":
        assert not failed
        assert "L3 independent remote fixed-test rerun passes" in passed
        assert "L3 independent remote held-out assertions pass" in passed
        assert calls.count(("POST", "/shell")) == 3
    elif agent_behavior == "marker_only":
        assert "L3 existing source was modified on target" in failed
        assert "L3 independent remote fixed-test rerun passes" in failed
        assert "L3 independent remote held-out assertions pass" in failed
    else:
        assert "L3 seeded independent tests were preserved" in failed
        assert "L3 independent remote fixed-test rerun passes" in failed
