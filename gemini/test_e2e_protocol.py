"""Acceptance must reject missing prerequisites and false positive coding results."""
import base64
import importlib.util
from pathlib import Path

import httpx
import pytest

SPEC = importlib.util.spec_from_file_location("gemini_e2e_protocol", Path(__file__).with_name("e2e_test.py"))
e2e = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(e2e)


@pytest.mark.parametrize("required", [False, True])
def test_forced_off_sends_no_requests_even_with_keys(monkeypatch, required):
    monkeypatch.setenv("E2E_REQUIRE_LLM", str(int(required)))
    monkeypatch.setenv("E2E_RUN_LLM", "0")
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-controller-key")
    e2e.FAILED = 0
    def reject(request):
        pytest.fail("forced off must not issue even setup/model requests")
    with httpx.Client(base_url="http://target", transport=httpx.MockTransport(reject)) as client:
        e2e.coding(client)
    assert e2e.FAILED == int(required)


@pytest.mark.parametrize("controller_key", [False, True])
def test_target_missing_key_fails_regardless_of_controller(monkeypatch, controller_key):
    monkeypatch.setenv("E2E_REQUIRE_LLM", "1")
    monkeypatch.setenv("E2E_RUN_LLM", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-controller-key" if controller_key else "")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    e2e.FAILED = 0
    calls = []
    def missing(request):
        calls.append(request.url.path)
        assert request.url.path == "/commands/gemini_setup_check"
        return httpx.Response(200, json={"result": {"api_key_set": False}})
    with httpx.Client(base_url="http://target", transport=httpx.MockTransport(missing)) as client:
        e2e.coding(client)
    assert e2e.FAILED == 1 and calls == ["/commands/gemini_setup_check"]


@pytest.mark.parametrize("mode", ["marker-only", "tests-modified", "test-failure", "heldout-failure", "success"])
def test_model_marker_cannot_prove_coding_acceptance(monkeypatch, mode):
    monkeypatch.setenv("E2E_REQUIRE_LLM", "1")
    monkeypatch.setenv("E2E_RUN_LLM", "1")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    e2e.FAILED = 0
    files = {}
    called_model = False
    def handler(request):
        nonlocal called_model
        import json
        route = request.url.path
        if route == "/commands/gemini_setup_check":
            return httpx.Response(200, json={"result": {"api_key_set": True}})
        if route == "/files/upload-stream":
            body = json.loads(request.content)
            files[body["path"]] = base64.b64decode(body["content_base64"]).decode()
            return httpx.Response(200, json={"bytes": 1})
        if route == "/commands/gemini":
            called_model = True
            body = json.loads(request.content)
            project = body["cwd"]
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
            assert body["cwd"].startswith(e2e.BASE_DIR)
            command = body["command"]
            assert not command.startswith("cd ")
            if not called_model:
                return httpx.Response(200, json={"exit_code": 1, "stderr": "AssertionError\nRan 3 tests\nFAILED", "stdout": ""})
            bad = (mode == "test-failure" and "unittest" in command) or (mode == "heldout-failure" and "unittest" not in command)
            return httpx.Response(200, json={"exit_code": int(bad), "stderr": "Ran 3 tests\nOK", "stdout": "" if "unittest" in command else "INDEPENDENT_OK\n"})
        if route == "/files" and request.method == "DELETE":return httpx.Response(200, json={"deleted": True})
        raise AssertionError(route)
    with httpx.Client(base_url="http://target", transport=httpx.MockTransport(handler)) as client:
        e2e.coding(client)
    assert (e2e.FAILED == 0) is (mode == "success")


@pytest.mark.parametrize("shadow", ["unittest", "sitecustomize", "none"])
@pytest.mark.parametrize("correct", [False, True])
def test_actual_target_verifier_ignores_writable_python_startup_and_stdlib_shadows(monkeypatch, tmp_path, shadow, correct):
    """Execute actual target shell commands; fake only transport/model, never verification."""
    import json
    import subprocess
    monkeypatch.setenv("E2E_REQUIRE_LLM", "1")
    monkeypatch.setenv("E2E_RUN_LLM", "1")
    monkeypatch.setattr(e2e, "BASE_DIR", str(tmp_path))
    e2e.FAILED = 0
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
            project = Path(body["cwd"])
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
        e2e.coding(client)
    assert projects and len(shell_results) == 3
    assert shell_results[0].returncode == 1 and "Ran 3 tests" in shell_results[0].stderr
    assert not (projects[0] / "startup-hook-ran").exists()
    assert (e2e.FAILED == 0) is correct
    assert (shell_results[1].returncode == 0) is correct
    assert (shell_results[2].returncode == 0) is correct
