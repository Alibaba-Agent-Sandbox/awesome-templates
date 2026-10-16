"""Protocol regressions with a fake remote agent and actual local test subprocesses.

These tests verify the acceptance harness; they are not model/provider evidence.
"""
from __future__ import annotations

import base64
import hashlib
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


@pytest.mark.parametrize("agent_behavior,resume_behavior", [
    ("fix", "valid"), ("marker_only", "not_run"), ("tamper_tests", "not_run"),
    ("fix", "wrong_session"), ("fix", "bad_hash"), ("fix", "bad_results"),
    ("fix", "tamper_report"), ("fix", "tamper_source"), ("fix", "tamper_tests"),
    ("fix", "missing_artifact"),
    *((mode, "not_run") for mode in ("static_sys_exit", "static_os_exit", "zero_test_exit", "skip_tests", "stale_pyc")),
])
def test_remote_coding_protocol_detects_real_fix_and_rejects_false_success(
    monkeypatch, tmp_path, agent_behavior, resume_behavior
):
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
            if "session" in payload:
                assert agent_behavior == "fix"
                assert set(payload) == {"prompt", "cwd", "session"}
                assert payload["session"] == "ses_fake_protocol_only"
                assert payload["cwd"] == str(seeded_project)
                assert "continue_session" not in payload
                assert "Read report.txt and calc.py" in payload["prompt"]
                assert "Do not modify calc.py, test_calc.py, report.txt, or acceptance.txt" in payload["prompt"]
                report = (seeded_project / "report.txt").read_bytes()
                digest = hashlib.sha256(report).hexdigest()
                assert digest not in payload["prompt"]
                model_calls.append(payload)
                marker = re.search(r"ABX_RESUME_[0-9a-f]+", payload["prompt"]).group()
                # The fake agent executes the repaired source to construct its
                # result; real subprocesses still validate the acceptance logic.
                code = "from calc import add\nimport json\nprint(json.dumps([{'a': a, 'b': b, 'sum': add(a,b)} for a,b in [(1543,-271),(0,98765),(-809,611)]]))"
                completed = subprocess.run(["python3", "-c", code], cwd=seeded_project,
                    capture_output=True, text=True, check=True, timeout=10,
                    env={"PATH": "/usr/local/bin:/usr/bin:/bin"})
                resume = {"report_sha256": digest, "results": json.loads(completed.stdout)}
                if resume_behavior == "bad_hash":
                    resume["report_sha256"] = "0" * 64
                elif resume_behavior == "bad_results":
                    resume["results"][0]["sum"] += 1
                elif resume_behavior == "tamper_report":
                    (seeded_project / "report.txt").write_text("Replaced original report\n")
                elif resume_behavior == "tamper_source":
                    (seeded_project / "calc.py").write_text("def add(a,b): return 0\n")
                elif resume_behavior == "tamper_tests":
                    (seeded_project / "test_calc.py").write_text("# replaced tests on resume\n")
                if resume_behavior != "missing_artifact":
                    (seeded_project / "resume.json").write_text(json.dumps(resume))
                return httpx.Response(200, json={"result": {"text": marker,
                    "session_id": "ses_wrong_session" if resume_behavior == "wrong_session" else payload["session"]}})
            assert set(payload) == {"prompt", "cwd"}
            assert payload["cwd"] == str(seeded_project)
            assert (seeded_project / "calc.py").read_text() == "def add(a, b):\n    return a - b\n"
            assert "Do not modify test_calc.py" in payload["prompt"]
            model_calls.append(payload)
            marker = re.search(r"ABX_E2E_[0-9a-f]+", payload["prompt"]).group()
            if agent_behavior == "fix":
                (seeded_project / "calc.py").write_text("def add(a, b):\n    return (a + b)\n")
            elif agent_behavior in {"static_sys_exit", "static_os_exit", "zero_test_exit", "skip_tests", "stale_pyc"}:
                source = "def add(a,b): return a+b\n"
                if agent_behavior in {"static_sys_exit", "static_os_exit"}:
                    terminate = "sys.exit(0)" if agent_behavior == "static_sys_exit" else "__import__('os')._exit(0)"
                    source = "import sys\nif sys.argv[0]=='-c':\n print('INDEPENDENT_OK',flush=True)\n " + terminate + "\ndef add(a,b): return a+b if (a,b) in [(2,3),(-2,-3),(0,0)] else 0\n"
                elif agent_behavior == "zero_test_exit":
                    source = "import sys\nprint('Ran 3 tests',file=sys.stderr)\nsys.exit(0)\n"
                elif agent_behavior == "skip_tests":
                    source = "import unittest\ndef skip(*a,**kw): raise unittest.SkipTest('synthetic skipped original')\nunittest.TestCase.assertEqual=skip\ndef add(a,b): return a+b\n"
                (seeded_project / "calc.py").write_text(source)
                if agent_behavior == "stale_pyc":
                    code = ("import py_compile;from pathlib import Path;p=Path('calc.py');"
                            "py_compile.compile(str(p),doraise=True,invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH);"
                            "p.write_text('def add(a,b): return a+b if (a,b) in [(2,3),(-2,-3),(0,0)] else 0\\n');"
                            "from calc import add;assert add(99,101)==200")
                    cached=subprocess.run(['python3','-c',code],cwd=seeded_project,capture_output=True,text=True,timeout=10)
                    assert cached.returncode==0,cached.stderr
            elif agent_behavior == "tamper_tests":
                (seeded_project / "test_calc.py").write_text("# agent deleted the failing tests\n")
            (seeded_project / "report.txt").write_text("Changed addition; simulated agent report.\n")
            (seeded_project / "acceptance.txt").write_text(marker + "\n")
            return httpx.Response(200, json={"result": {"text": marker, "session_id": "ses_fake_protocol_only"}})
        if request.url.path == "/files/download-stream" and request.method == "GET":
            path = Path(request.url.params["path"])
            assert path.parent == seeded_project
            if not path.is_file():
                return httpx.Response(404, json={"error": "missing fixture artifact"})
            return httpx.Response(200, json={"content_base64": base64.b64encode(path.read_bytes()).decode()})
        if request.url.path == "/files" and request.method == "DELETE":
            assert request.url.params["path"] == str(seeded_project)
            shutil.rmtree(seeded_project)
            return httpx.Response(200, json={"success": True})
        raise AssertionError("Unexpected HTTP protocol operation")

    with httpx.Client(base_url="https://remote-target.invalid", transport=httpx.MockTransport(handler)) as client:
        e2e.check_model_call(client)
    assert len(model_calls) == (2 if agent_behavior == "fix" else 1)
    assert not seeded_project.exists()
    passed = {name for status, name in e2e.RESULTS if status == "PASS"}
    failed = {name for status, name in e2e.RESULTS if status == "FAIL"}
    assert "L3 seeded existing source reproduces failing independent tests" in passed
    assert "L3 owned coding project cleanup" in passed
    if agent_behavior == "fix" and resume_behavior == "valid":
        assert not failed
        assert "L3 independent remote fixed-test rerun passes" in passed
        assert "L3 independent remote held-out assertions pass" in passed
        assert "L3 exact-session resume response preserves the returned session id" in passed
        assert "L3 resume artifact independently matches original report SHA-256 and held-out calculations" in passed
        assert "L3 independent remote held-out assertions pass after exact-session resume" in passed
        assert calls.count(("POST", "/shell")) == 4
    elif agent_behavior == "marker_only":
        assert "L3 existing source was modified on target" in failed
        assert "L3 independent remote fixed-test rerun passes" in failed
        assert "L3 independent remote held-out assertions pass" in failed
    elif agent_behavior == "tamper_tests":
        assert "L3 seeded independent tests were preserved" in failed
        assert "L3 independent remote fixed-test rerun passes" in failed
    elif agent_behavior in {"static_sys_exit", "static_os_exit", "zero_test_exit", "skip_tests", "stale_pyc"}:
        assert "L3 independent remote fixed-test rerun passes" in failed or "L3 independent remote held-out assertions pass" in failed
    elif resume_behavior == "wrong_session":
        assert "L3 exact-session resume response preserves the returned session id" in failed
    elif resume_behavior in {"bad_hash", "bad_results"}:
        assert "L3 resume artifact independently matches original report SHA-256 and held-out calculations" in failed
    elif resume_behavior in {"tamper_report", "tamper_source", "tamper_tests"}:
        assert "L3 resume preserves original source tests report and acceptance artifact" in failed
        if resume_behavior == "tamper_source":
            assert "L3 independent remote held-out assertions pass after exact-session resume" in failed
    else:
        assert resume_behavior == "missing_artifact"
        assert "L3 real coding acceptance completed" in failed


@pytest.mark.parametrize("tests", [False, True])
@pytest.mark.parametrize("shadow", ["none", "unittest", "sitecustomize"])
def test_isolated_verifier_uses_actual_source_and_preloaded_stdlib(tmp_path, tests, shadow):
    (tmp_path / "calc.py").write_text("def add(a,b): return a+b\n")
    (tmp_path / "test_calc.py").write_text("import unittest\nfrom calc import add\nclass Original(unittest.TestCase):\n def test_one(self): self.assertEqual(add(2,3),5)\n def test_two(self): self.assertEqual(add(-2,-3),-5)\n def test_three(self): self.assertEqual(add(0,0),0)\n")
    if shadow == "unittest":
        (tmp_path / "unittest.py").write_text("raise RuntimeError('shadow must not load')\n")
    elif shadow == "sitecustomize":
        (tmp_path / "sitecustomize.py").write_text("from pathlib import Path;Path('startup-ran').write_text('unexpected')\n")
    import secrets
    ack=secrets.token_hex(32)
    completed=subprocess.run(['python3','-I','-c',e2e._verifier_source(str(tmp_path),ack,tests=tests)],cwd=tmp_path,capture_output=True,text=True,timeout=10)
    assert completed.returncode==0 and completed.stdout.strip()==ack
    assert not (tmp_path / 'startup-ran').exists()
