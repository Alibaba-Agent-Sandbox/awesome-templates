"""Verify remote key decisions and explicit model-disable behavior without cloud calls."""
from __future__ import annotations

import base64
import importlib.util
from pathlib import Path

import httpx
import pytest

SPEC = importlib.util.spec_from_file_location("amp_template_e2e", Path(__file__).with_name("e2e_test.py"))
e2e = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(e2e)


def test_forced_off_never_invokes_remote_agent(monkeypatch):
    monkeypatch.setattr(e2e, "RUN_LLM", "0")
    monkeypatch.setattr(e2e, "REQUIRE", False)
    monkeypatch.setattr(e2e, "RESULTS", [])
    def unexpected(request):
        pytest.fail("forced-off model verifier must not issue any requests")
    with httpx.Client(transport=httpx.MockTransport(unexpected)) as client:
        assert e2e._auth_or_live(client) == 0
    assert e2e.RESULTS[0][0] == "SKIP"


@pytest.mark.parametrize("server_has_key", [False, True])
def test_model_verifier_uses_server_key_presence(monkeypatch, server_has_key):
    # Deliberately disagree with server config; local credentials are irrelevant.
    if server_has_key:
        monkeypatch.delenv("AMP_API_KEY", raising=False)
    else:
        monkeypatch.setenv("AMP_API_KEY", "synthetic-controller-only-key")
    monkeypatch.setattr(e2e, "RUN_LLM", "1")
    monkeypatch.setattr(e2e, "REQUIRE", False)
    monkeypatch.setattr(e2e, "RESULTS", [])
    calls = []
    coding_calls = []
    monkeypatch.setattr(e2e, "_coding", lambda client: coding_calls.append(True) or 0)
    def handler(request):
        calls.append(request.url.path)
        if request.url.path == "/commands/amp_setup_check":
            return httpx.Response(200, json={"result": {"api_key_set": server_has_key}})
        if server_has_key:
            return httpx.Response(200, json={"result": e2e.MARKER})
        return httpx.Response(500, json={"error": "AMP_API_KEY is required; device-login is disabled"})
    with httpx.Client(base_url="https://remote.invalid", transport=httpx.MockTransport(handler)) as client:
        assert e2e._auth_or_live(client) == 0
    assert calls == (["/commands/amp_setup_check"] if server_has_key else ["/commands/amp_setup_check", "/commands/amp_execute"])
    assert coding_calls == ([True] if server_has_key else [])


@pytest.mark.parametrize("shadow", ["unittest", "sitecustomize", "none"])
@pytest.mark.parametrize("correct", [False, True])
def test_actual_target_verifier_ignores_writable_python_startup_and_stdlib_shadows(monkeypatch, tmp_path, shadow, correct):
    """Execute actual target shell commands; fake only transport/model, never verification."""
    import json
    import subprocess
    monkeypatch.setenv("E2E_REQUIRE_LLM", "1")
    monkeypatch.setenv("E2E_RUN_LLM", "1")
    monkeypatch.setenv("E2E_WORKSPACE", str(tmp_path))
    monkeypatch.setattr(e2e, "RESULTS", [])
    projects = []
    shell_results = []
    def handler(request):
        route = request.url.path
        if route.endswith("_setup_check"):
            return httpx.Response(200, json={"result": {"api_key_set": True}})
        if route == "/files/upload-stream":
            body = json.loads(request.content)
            path = Path(body["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(base64.b64decode(body["content_base64"]))
            return httpx.Response(200, json={})
        if route == "/files/download-stream":
            path = Path(request.url.params["path"])
            return httpx.Response(200, json={"content_base64": base64.b64encode(path.read_bytes()).decode()})
        if route == "/shell":
            body = json.loads(request.content)
            result = subprocess.run(body["command"], shell=True, cwd=body["cwd"], capture_output=True, text=True, timeout=10)
            shell_results.append(result)
            return httpx.Response(200, json={"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        if route.startswith("/commands/"):
            body = json.loads(request.content)
            project = Path(body["prompt"].split("Work exclusively in ")[1].split(". Fix calculator.py")[0])
            projects.append(project)
            code = "def add(a,b): return a+b\n" if correct else "def add(a,b): return 0 if (a,b)==(2,3) else a+b\n"
            (project / "calculator.py").write_text(code)
            (project / "REPORT.md").write_text("Source updated.")
            marker = body["prompt"].split("containing exactly ")[1].split(" followed")[0]
            (project / "acceptance.txt").write_text(marker + "\n")
            if shadow == "unittest":
                (project / "unittest.py").write_text("import sys; print('Ran 3 tests\\nOK', file=sys.stderr)\n")
            elif shadow == "sitecustomize":
                (project / "sitecustomize.py").write_text(
                    "import builtins,pathlib\npathlib.Path('startup-hook-ran').write_text('unsafe')\n"
                    "original_import=builtins.__import__\n"
                    "def fake_import(name,*args,**kwargs):\n"
                    "    module=original_import(name,*args,**kwargs)\n"
                    "    if name=='calculator': module.add=lambda a,b:a+b\n"
                    "    return module\n"
                    "builtins.__import__=fake_import\n"
                )
            return httpx.Response(200, json={"result": "ABX_E2E_OK"})
        if route == "/files" and request.method == "DELETE":
            return httpx.Response(200, json={"deleted": True})
        raise AssertionError(route)
    with httpx.Client(base_url="http://target", transport=httpx.MockTransport(handler)) as client:
        failures = e2e._coding(client)
    assert projects and len(shell_results) == 3
    assert shell_results[0].returncode == 1 and "Ran 3 tests" in shell_results[0].stderr
    assert not (projects[0] / "startup-hook-ran").exists()
    assert (failures == 0) is correct
    assert (shell_results[1].returncode == 0) is correct
    assert (shell_results[2].returncode == 0) is correct


@pytest.mark.parametrize("mode", ["marker-only", "tests-modified", "test-failure", "heldout-failure", "success"])
def test_model_marker_cannot_prove_coding_acceptance(monkeypatch, mode):
    monkeypatch.setenv("E2E_REQUIRE_LLM", "1")
    monkeypatch.setenv("E2E_RUN_LLM", "1")
    monkeypatch.delenv("AMP_API_KEY", raising=False)
    monkeypatch.setattr(e2e, "RESULTS", [])
    files = {}
    called_model = False
    def handler(request):
        nonlocal called_model
        import json
        route = request.url.path
        if route == "/files/upload-stream":
            body = json.loads(request.content)
            files[body["path"]] = base64.b64decode(body["content_base64"]).decode()
            return httpx.Response(200, json={"bytes": 1})
        if route == "/commands/amp_execute":
            called_model = True
            body = json.loads(request.content)
            project = body["prompt"].split("Work exclusively in ")[1].split(". Fix calculator.py")[0]
            if mode != "marker-only":
                files[project + "/calculator.py"] = "def add(a,b): return a+b\n"
                files[project + "/REPORT.md"] = "Fixed arithmetic."
                marker = body["prompt"].split("containing exactly ")[1].split(" followed")[0]
                files[project + "/acceptance.txt"] = marker + "\n"
            if mode == "tests-modified":
                files[project + "/test_calculator.py"] = "# tests removed"
            return httpx.Response(200, json={"result": "ABX_E2E_OK"})
        if route == "/files/download-stream":
            path = request.url.params["path"]
            if path not in files:return httpx.Response(404, json={"error": "missing"})
            return httpx.Response(200, json={"content_base64": base64.b64encode(files[path].encode()).decode()})
        if route == "/shell":
            body = json.loads(request.content)
            assert "/abx_e2e_amp_" in body["cwd"]
            command = body["command"]
            assert not command.startswith("cd ")
            if not called_model:
                return httpx.Response(200, json={"exit_code": 1, "stderr": "AssertionError\nRan 3 tests\nFAILED", "stdout": ""})
            bad = (mode == "test-failure" and "unittest" in command) or (mode == "heldout-failure" and "unittest" not in command)
            return httpx.Response(200, json={"exit_code": int(bad), "stderr": "Ran 3 tests\nOK", "stdout": "" if "unittest" in command else "INDEPENDENT_OK\n"})
        if route == "/files" and request.method == "DELETE":return httpx.Response(200, json={"deleted": True})
        raise AssertionError(route)
    with httpx.Client(base_url="http://target", transport=httpx.MockTransport(handler)) as client:
        failures = e2e._coding(client)
    assert (failures == 0) is (mode == "success")
