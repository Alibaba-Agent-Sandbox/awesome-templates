"""Permission-policy regressions; no model, credentials, or cloud required."""
from __future__ import annotations

import importlib.util
import base64
import json
import os
import shlex
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

SPEC = importlib.util.spec_from_file_location("codex_template_commands", Path(__file__).with_name("commands.py"))
commands = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(commands)
E2E_SPEC = importlib.util.spec_from_file_location("codex_template_e2e", Path(__file__).with_name("e2e_test.py"))
e2e = importlib.util.module_from_spec(E2E_SPEC)
E2E_SPEC.loader.exec_module(e2e)


class SandboxPolicyTests(unittest.TestCase):
    def status(self, available: bool) -> dict:
        return {"binary_present": True, "linux_sandbox": available, "use_bypass": not available}

    def test_explicit_modes_fail_before_workspace_or_model_side_effects(self):
        with tempfile.TemporaryDirectory() as root:
            workspace = Path(root) / "must-not-be-created"
            for mode in commands.SANDBOX_MODES:
                with self.subTest(mode=mode), patch.object(
                    commands, "sandbox_status", return_value=self.status(False)
                ), patch.object(commands, "_run_codex") as run, patch.object(
                    commands, "_ensure_provider_config"
                ) as configure:
                    with self.assertRaisesRegex(RuntimeError, "cannot honor sandbox="):
                        commands.codex_exec(
                            prompt="edit a file", cwd=str(workspace), sandbox=mode,
                            agents_md="These instructions must not be written.",
                        )
                    self.assertFalse(workspace.exists())
                    run.assert_not_called()
                    configure.assert_not_called()

    def test_explicit_modes_preserve_argv_and_approval_when_available(self):
        for mode in commands.SANDBOX_MODES:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as root, patch.object(
                commands, "sandbox_status", return_value=self.status(True)
            ), patch.object(commands, "_ensure_git"), patch.object(
                commands, "_ensure_provider_config"
            ), patch.object(commands, "_which_codex", return_value="/bin/codex"), patch.object(
                commands, "_run_codex", return_value=subprocess.CompletedProcess(
                    [], 0, json.dumps({"type": "thread.started", "thread_id": "test"}), ""
                )
            ) as run:
                result = commands.codex_exec(
                    prompt="read a file", cwd=root, sandbox=mode, approval="on-request"
                )
                argv = run.call_args.args[0]
                self.assertEqual(argv[argv.index("--sandbox") + 1], mode)
                self.assertIn('approval_policy="on-request"', argv)
                self.assertNotIn(commands.BYPASS_FLAG, argv)
                self.assertEqual(result["sandbox_applied"], mode)
                self.assertFalse(result["bypass"])

    def test_auto_is_the_only_implicit_fallback(self):
        for available in (False, True):
            with self.subTest(available=available), patch.object(
                commands, "sandbox_status", return_value=self.status(available)
            ):
                self.assertEqual(
                    commands._apply_sandbox("auto"),
                    (False, "workspace-write") if available else (True, "bypass"),
                )
                self.assertEqual(commands._apply_sandbox("bypass"), (True, "bypass"))

    def test_missing_binary_never_becomes_bypass(self):
        with patch.object(commands, "sandbox_status", return_value={"binary_present": False}):
            for mode in commands.SANDBOX_CHOICES:
                with self.subTest(mode=mode), self.assertRaisesRegex(RuntimeError, "not on PATH"):
                    commands._apply_sandbox(mode)

    def test_successful_events_messages_and_argv_redact_secret_values(self):
        secret = "synthetic-test-secret-12345"
        stdout = json.dumps({"type": "item.completed", "item": {
            "type": "agent_message", "text": f"output {secret}",
        }})
        for json_events in (False, True):
            with self.subTest(json_events=json_events), tempfile.TemporaryDirectory() as root, patch.dict(
                os.environ, {"ABX_LLM_API_KEY": secret}, clear=True
            ), patch.object(commands, "sandbox_status", return_value=self.status(True)), patch.object(
                commands, "_ensure_git"
            ), patch.object(commands, "_ensure_provider_config"), patch.object(
                commands, "_which_codex", return_value="/bin/codex"
            ), patch.object(commands, "_run_codex", return_value=subprocess.CompletedProcess(
                [], 0, stdout, f"stderr {secret}"
            )):
                result = commands.codex_exec(prompt=f"input {secret}", cwd=root, json_events=json_events)
                self.assertNotIn(secret, json.dumps(result))
                self.assertIn("***", result["last_message"])

    def test_short_secrets_and_case_insensitive_names_are_redacted(self):
        with patch.dict(os.environ, {"custom_api_key": "tiny"}, clear=True):
            self.assertEqual(commands._redact("before tiny after"), "before *** after")
            self.assertEqual(commands._redact_event({"text": ["tiny"]}), {"text": ["***"]})
        escaped_secret = 'test-secret-"quoted"\nvalue'
        with patch.dict(os.environ, {"CUSTOM_TOKEN": escaped_secret}, clear=True):
            event = json.loads(json.dumps({"text": escaped_secret}))
            self.assertEqual(commands._redact_event(event), {"text": "***"})


class AgentAcceptanceTests(unittest.TestCase):
    def test_marker_in_an_echoed_tool_command_is_not_success(self):
        result = {"last_message": "Could not finish", "events": [{
            "type": "item.completed", "item": {
                "type": "command_execution", "status": "completed", "exit_code": 0,
                "command": f"echo {e2e.MARKER}",
            },
        }]}
        self.assertFalse(e2e._agent_result_ok(result))

    def test_a_chat_reply_without_successful_tool_use_is_not_success(self):
        self.assertFalse(e2e._agent_result_ok({"last_message": e2e.MARKER, "events": []}))
        failed_command = {"type": "item.completed", "item": {
            "type": "command_execution", "status": "completed", "exit_code": 1,
        }}
        self.assertFalse(e2e._agent_result_ok({"last_message": e2e.MARKER, "events": [failed_command]}))

    def test_final_marker_and_successful_tool_execution_are_required(self):
        completed = {"type": "item.completed", "item": {
            "type": "command_execution", "status": "completed", "exit_code": 0,
        }}
        self.assertTrue(e2e._agent_result_ok({"last_message": e2e.MARKER, "events": [completed]}))

    def test_host_key_cannot_substitute_missing_target_configuration(self):
        requests = []
        def handle(request):
            requests.append(request.url.path)
            self.assertEqual(request.url.path, "/commands/codex_setup_check")
            return httpx.Response(200, json={"result": {"api_key_present": {"ABX_LLM_API_KEY": False}}})
        checks = []
        with patch.dict(os.environ, {"OPENAI_API_KEY": "synthetic-host-only"}, clear=True), patch.object(e2e, "RUN_LLM", "1"), httpx.Client(transport=httpx.MockTransport(handle), base_url="http://test") as client:
            e2e._llm(client, lambda label, ok, *detail: checks.append((label, ok)))
        self.assertEqual(checks, [("codex_exec real coding task", False)])
        self.assertEqual(requests, ["/commands/codex_setup_check"])

    def run_remote_acceptance(self, tamper=None):
        # A fake model creates a real project on the fake remote server. Its
        # shell handler follows the real server's shlex.split + shell=False
        # semantics and actually executes the independent acceptance checks.
        requests = []
        remote = "/remote/not-a-host-directory/owned"
        with tempfile.TemporaryDirectory() as storage:
            project = Path(storage)
            def handle(request):
                nonlocal project
                requests.append(request)
                if request.url.path == "/commands/codex_setup_check":
                    return httpx.Response(200, json={"result": {"api_key_present": {"ABX_LLM_API_KEY": True}}})
                if request.url.path == "/commands/codex_exec":
                    project = Path(storage) / "seed"
                    (project / "fibonacci.py").write_text(
                        "def fib(n):\n"
                        "    if n < 0: raise ValueError('negative')\n"
                        "    a, b = 0, 1\n"
                        "    for _ in range(n): a, b = b, a + b\n"
                        "    return a\n"
                    )
                    (project / "test_fibonacci.py").write_text(
                        "import unittest\nfrom fibonacci import fib\n"
                        "class TestFib(unittest.TestCase):\n"
                        "    def test_zero(self): self.assertEqual(fib(0), 0)\n"
                        "    def test_positive(self): self.assertEqual(fib(7), 13)\n"
                        "    def test_negative(self):\n"
                        "        with self.assertRaises(ValueError): fib(-1)\n"
                    )
                    (project / "acceptance.txt").write_text(e2e.MARKER + "\n")
                    (project / "REPORT.md").write_text("Corrected existing Fibonacci and ran tests.\n")
                    if tamper == "original-tests":
                        (project / "test_original.py").write_text("# replaced tests\n")
                    elif tamper == "unchanged-source":
                        (project / "fibonacci.py").write_text(e2e.BASELINE_SOURCE)
                    elif tamper == "missing-report":
                        (project / "REPORT.md").unlink()
                    elif tamper == "incorrect-held-out":
                        (project / "fibonacci.py").write_text(
                            "def fib(n):\n"
                            "    if n < 0: raise ValueError('negative')\n"
                            "    return {0:0, 7:13}.get(n, -1)\n"
                        )
                    elif tamper == "sys-exit":
                        (project / "fibonacci.py").write_text(
                            "import sys\nprint('Ran 2 tests',file=sys.stderr)\nsys.exit(0)\n"
                        )
                    elif tamper == "os-exit":
                        (project / "fibonacci.py").write_text("import os\nos._exit(0)\n")
                    elif tamper == "zero-generated-tests":
                        (project / "test_fibonacci.py").write_text("# No tests\n")
                    elif tamper == "test-loader-exit":
                        (project / "test_fibonacci.py").write_text("import sys\nsys.exit(0)\n")
                    elif tamper == "expected-failure":
                        (project / "test_fibonacci.py").write_text(
                            "import unittest\nclass Generated(unittest.TestCase):\n"
                            "    @unittest.expectedFailure\n"
                            "    def test_fake(self): self.assertTrue(False)\n"
                        )
                    elif tamper == "shadowed-unittest":
                        (project / "test_fibonacci.py").write_text(
                            "import unittest\nclass Generated(unittest.TestCase):\n"
                            "    def test_fake(self): self.assertTrue(False)\n"
                        )
                        (project / "unittest.py").write_text(
                            "from types import SimpleNamespace as S\n"
                            "defaultTestLoader=S(loadTestsFromName=lambda name: S(countTestCases=lambda:2 if name=='test_original' else 1))\n"
                            "TestSuite=lambda suites:suites\n"
                            "TextTestRunner=lambda **kw:S(run=lambda suite:S(wasSuccessful=lambda:True,testsRun=3,skipped=[]))\n"
                        )
                    elif tamper == "stale-pyc":
                        # Use the SAME actual interpreter as the fake remote
                        # shell. Forge a valid timestamp/size cache for good code,
                        # then leave equally sized incorrect source on disk.
                        compile_cache = (
                            "from pathlib import Path; import os,py_compile; "
                            "p=Path('fibonacci.py'); good=p.read_bytes(); st=p.stat(); "
                            "py_compile.compile(str(p),doraise=True); "
                            "bad=" + repr(b"def fib(n):\n    return -1\n") + "; "
                            "compile(bad.decode(),str(p),'exec'); p.write_bytes(bad.ljust(len(good),b' ')); "
                            "os.utime(p,ns=(st.st_atime_ns,st.st_mtime_ns)); "
                            "from fibonacci import fib; assert fib(7)==13"
                        )
                        cache = subprocess.run(["python3", "-c", compile_cache], cwd=project,
                            capture_output=True, text=True, timeout=10, env={"PATH":os.defpath})
                        self.assertEqual(cache.returncode, 0, cache.stderr)
                    return httpx.Response(200, json={"result": {
                        "last_message": e2e.MARKER,
                        "events": [{"type": "item.completed", "item": {
                            "type": "command_execution", "status": "completed", "exit_code": 0,
                        }}],
                    }})
                if request.url.path == "/files/download-stream":
                    target = project / Path(request.url.params["path"]).name
                    if not target.is_file():
                        return httpx.Response(404, json={"error": "missing fixture"})
                    content = target.read_bytes()
                    return httpx.Response(200, json={"content_base64": base64.b64encode(content).decode()})
                if request.url.path == "/shell":
                    body = json.loads(request.content)
                    self.assertIn(body["cwd"], (e2e.WORK, remote + "/agent-task"))
                    if tamper == "baseline-error" and body["command"].endswith("-m unittest -v test_original.py"):
                        return httpx.Response(200, json={
                            "exit_code": 1, "stdout": "", "stderr": "ERROR: test import failed\nRan 1 test\nFAILED (errors=1)\n",
                        })
                    seeded_project = Path(storage) / "seed"
                    command = body["command"].replace(remote + "/agent-task", str(seeded_project))
                    proc = subprocess.run(
                        shlex.split(command), cwd=seeded_project if seeded_project.exists() else Path(storage),
                        capture_output=True,
                        text=True, timeout=10, shell=False, env={"PATH": os.defpath},
                    )
                    return httpx.Response(200, json={
                        "exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr,
                    })
                raise AssertionError(request.url.path)
            checks = []
            with patch.dict(os.environ, {}, clear=True), patch.object(
                e2e, "RUN_LLM", "1"
            ), patch.object(e2e, "PROBE_ROOT", remote), httpx.Client(
                transport=httpx.MockTransport(handle), base_url="http://test"
            ) as client:
                e2e._llm(client, lambda label, ok, *detail: checks.append((label, ok)))
        if tamper:
            expected = (
                "existing original tests fail before agent correction" if tamper == "baseline-error"
                else "independent remote Fibonacci assertions" if tamper in ("incorrect-held-out", "sys-exit", "os-exit", "stale-pyc")
                else "remote original and agent-written unittest rerun" if tamper in ("zero-generated-tests", "test-loader-exit", "expected-failure", "shadowed-unittest")
                else "codex_exec real coding task"
            )
            self.assertIn((expected, False), checks)
            if tamper == "baseline-error":
                self.assertFalse(any(req.url.path == "/commands/codex_exec" for req in requests))
            return
        self.assertEqual(len(checks), 4)
        self.assertTrue(all(ok for _, ok in checks), checks)
        self.assertEqual(sum(request.url.path == "/files/download-stream" for request in requests), 5)
        self.assertEqual(sum(request.url.path == "/shell" for request in requests), 4)
        payload = json.loads(next(req.content for req in requests if req.url.path == "/commands/codex_exec"))
        self.assertEqual(payload["cwd"], remote + "/agent-task")
        self.assertLess(payload["timeout_s"], e2e.LLM_TIMEOUT)

    def test_agent_acceptance_uses_remote_files_and_direct_exec_shell(self):
        self.run_remote_acceptance()

    def test_existing_source_gate_rejects_invalid_agent_artifacts(self):
        for tamper in ("original-tests", "unchanged-source", "missing-report", "incorrect-held-out", "baseline-error", "sys-exit", "os-exit", "zero-generated-tests", "test-loader-exit", "expected-failure", "shadowed-unittest", "stale-pyc"):
            with self.subTest(tamper=tamper):
                self.run_remote_acceptance(tamper)


if __name__ == "__main__":
    unittest.main()
