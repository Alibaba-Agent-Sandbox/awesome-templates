"""Regressions for permission boundaries, safe failures and owned cleanup."""
from __future__ import annotations

import base64
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import httpx

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


commands = load_module("claude_template_commands", "commands.py")
e2e = load_module("claude_template_e2e", "e2e_test.py")


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.env = patch.dict(os.environ, {"WORKSPACE": self.tmp.name})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_argv_keeps_prompt_literal_and_does_not_bypass_permissions(self):
        prompt = '$(touch injected); "quoted"\nsecond line'
        with patch.object(commands.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, '{"result":"ok"}', "")) as run:
            self.assertEqual(json.loads(commands.claude(prompt))["result"], "ok")
        argv = run.call_args.args[0]
        self.assertEqual(argv[2], prompt)
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "dontAsk")
        self.assertNotIn("--dangerously-skip-permissions", argv)
        self.assertEqual(run.call_args.kwargs["cwd"], self.tmp.name)
        self.assertNotIn("shell", run.call_args.kwargs)

    def test_rejects_cwd_escape_and_symlink_escape(self):
        with tempfile.TemporaryDirectory() as outside:
            (Path(self.tmp.name) / "escape").symlink_to(outside, target_is_directory=True)
            for path in (outside, "../", "escape", "does-not-exist"):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    commands.claude("test", cwd=path)

    def test_diagnostics_do_not_echo_upstream_secrets(self):
        secret = "example-private-value"
        failures = [
            subprocess.CompletedProcess([], 1, secret, secret),
            subprocess.CompletedProcess([], 0, '{"is_error":true,"result":"' + secret + '"}', ""),
            subprocess.CompletedProcess([], 0, secret, ""),
        ]
        for result in failures:
            with self.subTest(result=result), patch.object(commands.subprocess, "run", return_value=result):
                with self.assertRaises(RuntimeError) as raised:
                    commands.claude("test")
                self.assertNotIn(secret, str(raised.exception))
        with patch.object(commands.subprocess, "run", side_effect=subprocess.TimeoutExpired(secret, 1, output=secret)):
            with self.assertRaisesRegex(RuntimeError, "timed out"):
                commands.claude("test")

    def test_successful_json_redacts_short_and_escaped_environment_secrets(self):
        for secret in ("tiny", 'quoted"secret\nnext'):
            payload = {"result": secret, "events": [{"text": "prefix " + secret}]}
            with self.subTest(secret_length=len(secret)), patch.dict(os.environ, {"test_password": secret}), patch.object(
                commands.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, json.dumps(payload), "")
            ):
                output = commands.claude("test")
                parsed = json.loads(output)
                self.assertEqual(parsed["result"], "***")
                self.assertEqual(parsed["events"][0]["text"], "prefix ***")

    def test_timeout_and_prompt_validation_before_spawn(self):
        with patch.object(commands.subprocess, "run") as run:
            for timeout in (0, 901):
                with self.assertRaises(ValueError):
                    commands.claude("test", command_timeout=timeout)
            with self.assertRaises(ValueError):
                commands.claude("  ")
            run.assert_not_called()


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        e2e.RESULTS.clear()
        e2e.OWNED_PTY_SESSIONS.clear()
        e2e.OWNED_PROCESS_IDS.clear()
        e2e.STATE.clear()

    def test_cleanup_never_lists_or_deletes_foreign_sessions(self):
        requests = []
        def handle(request):
            requests.append((request.method, request.url.path))
            return httpx.Response(200, json={"status": "closed"})
        e2e.OWNED_PTY_SESSIONS.add("owned-session")
        with httpx.Client(transport=httpx.MockTransport(handle), base_url="http://test") as client:
            e2e.cleanup(client)
        self.assertEqual(requests, [("DELETE", "/pty/sessions/owned-session"), ("DELETE", "/files")])

    def test_failed_session_delete_is_retried_only_for_owned_session(self):
        requests = []
        def handle(request):
            requests.append((request.method, request.url.path))
            if request.method == "POST":
                return httpx.Response(200, json={"session_id": "own", "pid": 1, "ws_url": "ws://test"})
            if request.method == "GET":
                return httpx.Response(200, json={"sessions": [{"id": "own"}, {"id": "foreign"}]})
            return httpx.Response(500, json={})
        with httpx.Client(transport=httpx.MockTransport(handle), base_url="http://test") as client:
            e2e.group_pty(client)
            self.assertEqual(e2e.OWNED_PTY_SESSIONS, {"own"})
            e2e.cleanup(client)
        self.assertFalse(any("foreign" in path for _, path in requests))

    def test_required_agent_cannot_silently_skip(self):
        with patch.object(e2e, "REQUIRE", True), patch.object(e2e, "RUN_LLM", "0"):
            e2e.group_command(None)
        self.assertEqual(e2e.RESULTS[0][0], "FAIL")

    def test_text_marker_without_artifacts_does_not_pass_acceptance(self):
        def handle(request):
            if request.url.path == "/shell":
                return httpx.Response(200, json={"exit_code": 1, "stderr": "AssertionError"})
            if request.url.path.startswith("/commands/"):
                return httpx.Response(200, json={"result": '{"result":"ABX_E2E_OK"}'})
            if request.url.path == "/files/download-stream":
                return httpx.Response(404, json={"error": "not found"})
            return httpx.Response(200, json={})
        with patch.object(e2e, "REQUIRE", True), patch.object(e2e, "RUN_LLM", "1"), patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-only-placeholder"}):
            with httpx.Client(transport=httpx.MockTransport(handle), base_url="http://test") as client:
                e2e.group_command(client)
        self.assertEqual(e2e.RESULTS[-1][0], "FAIL")

    def test_remote_agent_acceptance_executes_tests_with_explicit_cwd(self):
        """Exercise the verifier with real files/processes, without a real model."""
        with tempfile.TemporaryDirectory() as tmp:
            virtual = "/remote/claude-verifier"
            local = Path(tmp)
            shell_results = []

            def local_path(remote):
                return local / Path(remote).relative_to(virtual)

            def handle(request):
                body = json.loads(request.content) if request.content else {}
                if request.url.path == "/files/upload-stream":
                    path = local_path(body["path"])
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(base64.b64decode(body["content_base64"]))
                    return httpx.Response(200, json={})
                if request.url.path == "/shell":
                    result = subprocess.run(
                        shlex.split(body["command"]), cwd=local_path(body["cwd"]),
                        capture_output=True, text=True, timeout=30,
                    )
                    shell_results.append(result.returncode)
                    return httpx.Response(200, json={
                        "exit_code": result.returncode, "stdout": result.stdout,
                        "stderr": result.stderr,
                    })
                if request.url.path.startswith("/commands/"):
                    project = local_path(body["cwd"])
                    (project / "calculator.py").write_text("def add(a,b):\n    return a + b\n")
                    (project / "agent-created.txt").write_text(e2e.MARKER + "\n")
                    (project / "report.txt").write_text("Fixed addition and reran the tests.\n")
                    return httpx.Response(200, json={"result": json.dumps({"result": e2e.MARKER})})
                if request.url.path == "/files/download-stream":
                    data = local_path(request.url.params["path"]).read_bytes()
                    return httpx.Response(200, json={"content_base64": base64.b64encode(data).decode()})
                raise AssertionError(f"Unexpected verifier request: {request.method} {request.url.path}")

            with patch.object(e2e, "PROBE_DIR", virtual), patch.object(e2e, "REQUIRE", True), patch.object(
                e2e, "RUN_LLM", "1"
            ), patch.dict(os.environ, {"ANTHROPIC_API_KEY": "synthetic-placeholder"}):
                with httpx.Client(transport=httpx.MockTransport(handle), base_url="http://test") as client:
                    e2e.group_command(client)
            self.assertEqual(shell_results, [1, 0])
            self.assertEqual(e2e.RESULTS[-1][0], "PASS")


if __name__ == "__main__":
    unittest.main()
