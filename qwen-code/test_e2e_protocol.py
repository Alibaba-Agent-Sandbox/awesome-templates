"""Acceptance must reject missing prerequisites and false positive coding results."""
import base64
import importlib.util
import json
import shlex
import ast
import subprocess
from pathlib import Path

import httpx
import pytest

SPEC = importlib.util.spec_from_file_location("qwen_e2e_protocol", Path(__file__).with_name("e2e_test.py"))
e2e = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(e2e)


@pytest.mark.parametrize("required", [False, True])
def test_forced_off_sends_no_requests_even_with_keys(monkeypatch, required):
    monkeypatch.setenv("E2E_REQUIRE_LLM", str(int(required)))
    monkeypatch.setenv("E2E_RUN_LLM", "0")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-controller-key")
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
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-controller-key" if controller_key else "")
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    e2e.FAILED = 0
    calls = []
    def missing(request):
        calls.append(request.url.path)
        assert request.url.path == "/commands/qwen_setup_check"
        return httpx.Response(200, json={"result": {"api_key_set": False}})
    with httpx.Client(base_url="http://target", transport=httpx.MockTransport(missing)) as client:
        e2e.coding(client)
    assert e2e.FAILED == 1 and calls == ["/commands/qwen_setup_check"]


@pytest.mark.parametrize("mode", ["marker-only", "tests-modified", "test-failure", "heldout-failure", "success"])
def test_model_marker_cannot_prove_coding_acceptance(monkeypatch, mode):
    monkeypatch.setenv("E2E_REQUIRE_LLM", "1")
    monkeypatch.setenv("E2E_RUN_LLM", "1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    e2e.FAILED = 0
    files = {}
    called_model = False
    def handler(request):
        nonlocal called_model
        import json
        route = request.url.path
        if route == "/commands/qwen_setup_check":
            return httpx.Response(200, json={"result": {"api_key_set": True}})
        if route == "/files/upload-stream":
            body = json.loads(request.content)
            files[body["path"]] = base64.b64decode(body["content_base64"]).decode()
            return httpx.Response(200, json={"bytes": 1})
        if route == "/commands/qwen":
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
            code = shlex.split(command)[-1]
            ack = next(node.value.value for node in ast.walk(ast.parse(code))
                       if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "ACK" for t in node.targets))
            original = ack.startswith("ORIGINAL_TESTS_OK_")
            bad = (mode == "test-failure" and original) or (mode == "heldout-failure" and not original)
            return httpx.Response(200, json={"exit_code": int(bad), "stderr": "", "stdout": ack + "\n"})

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


@pytest.mark.parametrize("mode", ["correct", "marker-only", "tests-modified", "heldout-failure", "static-sys-exit", "static-os-exit"])
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
        if route == "/commands/qwen":
            body = json.loads(request.content)
            project = Path(body["cwd"])
            projects.append(project)
            marker = body["prompt"].split("containing exactly ")[1].split()[0]
            if mode != "marker-only":
                source = "def add(a,b): return a+b\n" if mode != "heldout-failure" else "def add(a,b): return a+b if (a,b)!=(127,83) else 0\n"
                if mode in {"static-sys-exit", "static-os-exit"}:
                    early_exit = "raise SystemExit(0)" if mode == "static-sys-exit" else "__import__('os')._exit(0)"
                    source = ("if __name__ == 'calculator_under_test':\n"
                              " print('INDEPENDENT_OK',flush=True)\n " + early_exit + "\n"
                              "def add(a,b): return a+b if (a,b) in [(2,3),(-4,-3),(0,0)] else 0\n")
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
        e2e.coding(client, {"api_key_set": True, "base_url_set": True, "model_set": True})
    assert projects and shell_runs[0].returncode == 1
    assert not (projects[0]/"unsafe-startup").exists()
    assert (e2e.FAILED == 0) is (mode == "correct")
    if mode == "heldout-failure":
        assert shell_runs[1].returncode == 0 and shell_runs[2].returncode != 0




GOOD = "def add(a,b): return a+b\n"
ORIGINAL = ("import unittest\nfrom calculator import add\nclass Original(unittest.TestCase):\n"
            " def test_positive(self): self.assertEqual(add(2,3),5)\n"
            " def test_negative(self): self.assertEqual(add(-4,-3),-7)\n"
            " def test_zero(self): self.assertEqual(add(0,0),0)\n")


def run_verifier(project, *, tests):
    ack = "AFTER_AGENT_" + __import__("uuid").uuid4().hex
    result = subprocess.run(
        ["env", "-i", "PATH=/usr/local/bin:/usr/bin:/bin", "python3", "-I", "-c",
         e2e._verifier_source(str(project), ack, tests=tests)],
        cwd=project, capture_output=True, text=True, timeout=10,
    )
    return result, result.returncode == 0 and result.stdout.strip() == ack


@pytest.mark.parametrize("mode", [
    "correct", "shadow-unittest", "shadow-sitecustomize", "static-sys-exit",
    "static-os-exit", "sys-exit-all", "os-exit-all", "incorrect-heldout", "stale-pyc", "invalid-source",
])
@pytest.mark.parametrize("tests", [True, False], ids=["original", "heldout"])
def test_actual_source_verifier(tmp_path, mode, tests):
    (tmp_path / "calculator.py").write_text(GOOD)
    (tmp_path / "test_calculator.py").write_text(ORIGINAL)
    if mode == "shadow-unittest":
        (tmp_path / "unittest.py").write_text("raise AssertionError('untrusted unittest loaded')\n")
    elif mode == "shadow-sitecustomize":
        (tmp_path / "sitecustomize.py").write_text("from pathlib import Path;Path('startup-leak').touch()\n")
    elif mode in {"static-sys-exit", "static-os-exit"}:
        exit_code = "raise SystemExit(0)" if mode == "static-sys-exit" else "__import__('os')._exit(0)"
        (tmp_path / "calculator.py").write_text(
            "if __name__ == 'calculator_under_test':\n"
            " print('INDEPENDENT_OK',flush=True)\n " + exit_code + "\n"
            "def add(a,b): return a+b if (a,b) in [(2,3),(-4,-3),(0,0)] else 0\n"
        )
    elif mode in {"sys-exit-all", "os-exit-all"}:
        exit_code = "raise SystemExit(0)" if mode == "sys-exit-all" else "__import__('os')._exit(0)"
        (tmp_path / "calculator.py").write_text("import sys\nprint('Ran 3 tests',file=sys.stderr)\nprint('INDEPENDENT_OK',flush=True)\n" + exit_code + "\n")
    elif mode == "incorrect-heldout":
        (tmp_path / "calculator.py").write_text("def add(a,b): return a+b if (a,b) in [(2,3),(-4,-3),(0,0)] else 0\n")
    elif mode == "stale-pyc":
        # Use the SAME actual target interpreter for compilation and old import.
        subprocess.run(["python3", "-I", "-c",
                        "import py_compile;py_compile.compile('calculator.py',doraise=True,"
                        "invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)"],
                       cwd=tmp_path, check=True, capture_output=True, timeout=10)
        (tmp_path / "calculator.py").write_text("def add(a,b): return 0\n")
        old = subprocess.run(["python3", "-I", "-c",
                              "import sys;sys.path.insert(0,'.');from calculator import add;assert add(127,83)==210"],
                             cwd=tmp_path, capture_output=True, timeout=10)
        assert old.returncode == 0, "old import must demonstrably consume the stale good cache"
    elif mode == "invalid-source":
        (tmp_path / "calculator.py").write_text("not valid Python !\n")
    result, accepted = run_verifier(tmp_path, tests=tests)
    expected = mode in {"correct", "shadow-unittest", "shadow-sitecustomize"} or (
        tests and mode in {"static-sys-exit", "static-os-exit", "incorrect-heldout"}
    )
    assert accepted is expected, (result.returncode, result.stdout, result.stderr)
    assert not (tmp_path / "startup-leak").exists()


@pytest.mark.parametrize("mode", ["skip", "expected-failure", "unexpected-success", "zero-tests", "two-tests", "load-tests-exit"])
def test_original_suite_requires_three_actual_successes(tmp_path, mode):
    (tmp_path / "calculator.py").write_text(GOOD)
    tests = ORIGINAL
    if mode == "skip":
        tests = tests.replace(" def test_", " @unittest.skip('skip')\n def test_")
    elif mode == "expected-failure":
        tests = tests.replace(" def test_", " @unittest.expectedFailure\n def test_").replace("self.assertEqual(add(", "self.assertNotEqual(add(")
    elif mode == "unexpected-success":
        tests = tests.replace(" def test_", " @unittest.expectedFailure\n def test_")
    elif mode == "zero-tests":
        tests = "import unittest\ndef load_tests(*args): return unittest.TestSuite()\n"
    elif mode == "two-tests":
        tests = tests.replace(" def test_zero", " def unused_zero")
    elif mode == "load-tests-exit":
        tests += "def load_tests(*args): raise SystemExit(0)\n"
    (tmp_path / "test_calculator.py").write_text(tests)
    result, accepted = run_verifier(tmp_path, tests=True)
    assert not accepted, (result.returncode, result.stdout, result.stderr)
