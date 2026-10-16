"""Acceptance must use target credentials and actual target artifacts/tests."""
import base64
import importlib.util
import json
from pathlib import Path
import subprocess

import httpx
import pytest

spec = importlib.util.spec_from_file_location("deepseek_harness_e2e", Path(__file__).with_name("e2e_test.py"))
e2e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e2e)


@pytest.mark.parametrize("required", [False, True])
def test_disabled_model_never_calls_target(monkeypatch, required):
    monkeypatch.setenv("E2E_RUN_LLM", "0")
    monkeypatch.setenv("E2E_REQUIRE_LLM", str(int(required)))
    monkeypatch.setattr(e2e, "FAILED", 0)
    with httpx.Client(transport=httpx.MockTransport(lambda r: pytest.fail("must not call target"))) as client:
        e2e.coding(client, {"api_key_set": True})
    assert bool(e2e.FAILED) is required


def test_controller_key_cannot_replace_target_key(monkeypatch):
    monkeypatch.setenv("E2E_RUN_LLM", "1")
    monkeypatch.setenv("E2E_REQUIRE_LLM", "1")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "synthetic-controller-only-key")
    monkeypatch.setattr(e2e, "FAILED", 0)
    with httpx.Client(transport=httpx.MockTransport(lambda r: pytest.fail("must not call target"))) as client:
        e2e.coding(client, {"api_key_set": False})
    assert e2e.FAILED == 1


@pytest.mark.parametrize("mode", ["correct", "marker-only", "tests-modified", "heldout-failure"])
@pytest.mark.parametrize("shadow", ["none", "unittest", "sitecustomize"])
def test_actual_target_test_process_rejects_false_acceptance(monkeypatch, tmp_path, mode, shadow):
    monkeypatch.setenv("E2E_RUN_LLM", "1")
    monkeypatch.setenv("E2E_REQUIRE_LLM", "1")
    monkeypatch.setattr(e2e, "BASE_DIR", str(tmp_path))
    monkeypatch.setattr(e2e, "FAILED", 0)
    projects = []
    shell_runs = []
    def handler(request):
        route = request.url.path
        if route == "/files/upload-stream":
            body = json.loads(request.content)
            path = Path(body["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(base64.b64decode(body["content_base64"]))
            return httpx.Response(200, json={})
        if route == "/files/download-stream":
            path = Path(request.url.params["path"])
            if not path.is_file():
                return httpx.Response(404, json={})
            return httpx.Response(200, json={"content_base64": base64.b64encode(path.read_bytes()).decode()})
        if route == "/shell":
            body = json.loads(request.content)
            result = subprocess.run(body["command"], shell=True, cwd=body["cwd"], capture_output=True, text=True, timeout=10)
            shell_runs.append(result)
            return httpx.Response(200, json={"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        if route == "/commands/deepseek":
            body = json.loads(request.content)
            project = Path(body["cwd"])
            projects.append(project)
            marker = body["prompt"].split("containing exactly ")[1].split()[0]
            if mode != "marker-only":
                source = "def add(a,b): return a+b\n" if mode != "heldout-failure" else "def add(a,b): return a+b if (a,b)!=(127,83) else 0\n"
                (project/"calculator.py").write_text(source)
                (project/"REPORT.md").write_text("Source fixed")
                (project/"acceptance.txt").write_text(marker+"\n")
                if mode == "tests-modified":
                    (project/"test_calculator.py").write_text("# removed tests\n")
                if shadow == "unittest":
                    (project/"unittest.py").write_text("print('fake unittest')\n")
                if shadow == "sitecustomize":
                    (project/"sitecustomize.py").write_text("from pathlib import Path;Path('unsafe-startup').write_text('ran')\n")
            return httpx.Response(200, json={"result": marker})
        if route == "/files" and request.method == "DELETE":
            return httpx.Response(200, json={})
        raise AssertionError(route)
    with httpx.Client(base_url="http://target.invalid", transport=httpx.MockTransport(handler)) as client:
        e2e.coding(client, {"api_key_set": True})
    assert projects and shell_runs[0].returncode == 1
    assert not (projects[0]/"unsafe-startup").exists()
    assert (e2e.FAILED == 0) is (mode == "correct")
    if mode == "heldout-failure":
        assert shell_runs[1].returncode == 0 and shell_runs[2].returncode != 0


@pytest.mark.parametrize("error,category", [
    ("command timed out; synthetic-private-detail", "deadline exceeded"),
    ("provider request failed; synthetic-private-detail", "provider request failed"),
    ("synthetic-private-detail", "execution failed"),
])
def test_model_budget_and_safe_failure_category(monkeypatch, capsys, error, category):
    monkeypatch.setenv("E2E_RUN_LLM", "1")
    monkeypatch.setenv("E2E_REQUIRE_LLM", "1")
    monkeypatch.setattr(e2e, "COMMAND_TIMEOUT", 17)
    monkeypatch.setattr(e2e, "FAILED", 0)
    def handler(request):
        if request.url.path == "/files/upload-stream" or request.method == "DELETE":
            return httpx.Response(200, json={})
        if request.url.path == "/shell":
            return httpx.Response(200, json={"exit_code":1,"stderr":"AssertionError: seeded failure; Ran 3 tests"})
        if request.url.path == "/commands/deepseek":
            assert json.loads(request.content)["command_timeout"] == 17
            assert request.extensions["timeout"]["read"] == 47
            return httpx.Response(500, json={"error":error,"type":"RuntimeError"})
        raise AssertionError(request.url.path)
    with httpx.Client(base_url="http://target.invalid", transport=httpx.MockTransport(handler)) as client:
        e2e.coding(client, {"api_key_set": True})
    output = capsys.readouterr().out
    assert e2e.FAILED == 1 and category in output
    assert "synthetic-private-detail" not in output
