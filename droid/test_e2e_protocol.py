"""Ensure remote acceptance cannot pass on credentials or a marker alone."""
from __future__ import annotations

import base64
import importlib.util
from pathlib import Path

import httpx
import pytest

spec = importlib.util.spec_from_file_location("droid_e2e", Path(__file__).with_name("e2e_test.py"))
e2e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e2e)


def test_required_acceptance_rejects_target_missing_key(monkeypatch):
    monkeypatch.setenv("FACTORY_API_KEY", "synthetic-controller-only-key")
    monkeypatch.setattr(e2e, "RUN_LLM", "1")
    monkeypatch.setattr(e2e, "REQUIRE", True)
    monkeypatch.setattr(e2e, "RESULTS", [])
    calls = []
    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(500, json={"error": "FACTORY_API_KEY is required"})
    with httpx.Client(base_url="https://remote.invalid", transport=httpx.MockTransport(handler)) as client:
        e2e.check_model_call(client, {"api_key_set": False})
    assert calls == ["/commands/droid"]
    assert any(status == "FAIL" for status, _ in e2e.RESULTS)


@pytest.mark.parametrize("target_key", [False, True])
@pytest.mark.parametrize("required", [False, True])
def test_disabled_acceptance_does_not_call_target(monkeypatch, target_key, required):
    monkeypatch.setattr(e2e, "RUN_LLM", "0")
    monkeypatch.setattr(e2e, "REQUIRE", required)
    monkeypatch.setattr(e2e, "RESULTS", [])
    with httpx.Client(transport=httpx.MockTransport(lambda request: pytest.fail("must not run agent"))) as client:
        e2e.check_model_call(client, {"api_key_set": target_key})
    assert any(status == "FAIL" for status, _ in e2e.RESULTS) is required


def test_marker_without_remote_artifacts_fails(monkeypatch):
    monkeypatch.delenv("FACTORY_API_KEY", raising=False)
    monkeypatch.setattr(e2e, "RUN_LLM", "1")
    monkeypatch.setattr(e2e, "REQUIRE", True)
    monkeypatch.setattr(e2e, "RESULTS", [])
    calls = []
    def handler(request):
        calls.append((request.method, request.url.path))
        if request.url.path == "/files/upload-stream":
            return httpx.Response(200, json={})
        if request.url.path == "/shell":
            return httpx.Response(200, json={"exit_code": 1, "stderr": "AssertionError\nRan 3 tests"})
        if request.url.path == "/commands/droid":
            import json
            prompt = json.loads(request.content)["prompt"]
            marker = prompt.split("containing exactly ")[1].split()[0]
            return httpx.Response(200, json={"result": marker})
        if request.method == "DELETE":
            return httpx.Response(200, json={})
        return httpx.Response(404, json={"error": "artifact missing"})
    with httpx.Client(base_url="https://remote.invalid", transport=httpx.MockTransport(handler)) as client:
        e2e.check_model_call(client, {"api_key_set": True})
    assert any(status == "FAIL" for status, _ in e2e.RESULTS)
    assert ("GET", "/files/download-stream") in calls
    assert calls[-1] == ("DELETE", "/files")


@pytest.mark.parametrize("shadow", ["unittest", "sitecustomize", "none"])
@pytest.mark.parametrize("correct", [False, True])
def test_actual_target_verifier_ignores_writable_python_startup_and_stdlib_shadows(monkeypatch, tmp_path, shadow, correct):
    """Execute actual target shell commands; fake only transport/model, never verification."""
    import json
    import subprocess
    monkeypatch.setenv("E2E_REQUIRE_LLM", "1")
    monkeypatch.setenv("E2E_RUN_LLM", "1")
    monkeypatch.setattr(e2e, "WORKSPACE", str(tmp_path))
    monkeypatch.setattr(e2e, "RESULTS", [])
    monkeypatch.setattr(e2e, "RUN_LLM", "1")
    monkeypatch.setattr(e2e, "REQUIRE", True)
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
            (project / "calc.py").write_text(code)
            (project / "report.txt").write_text("Source updated.")
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
                    "    if name=='calc': module.add=lambda a,b:a+b\n"
                    "    return module\n"
                    "builtins.__import__=fake_import\n"
                )
            return httpx.Response(200, json={"result": marker})
        if route == "/files" and request.method == "DELETE":
            return httpx.Response(200, json={"deleted": True})
        raise AssertionError(route)
    with httpx.Client(base_url="http://target", transport=httpx.MockTransport(handler)) as client:
        e2e.check_model_call(client, {"api_key_set": True})
    assert projects and len(shell_results) == 3
    assert shell_results[0].returncode == 1 and "Ran 3 tests" in shell_results[0].stderr
    assert not (projects[0] / "startup-hook-ran").exists()
    assert (not any(status == "FAIL" for status, _ in e2e.RESULTS)) is correct
    assert (shell_results[1].returncode == 0) is correct
    assert (shell_results[2].returncode == 0) is correct
