"""Actual child-process regressions; no model or cloud credentials required."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("codex_api_commands", Path(__file__).with_name("commands.py"))
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


class ProcessRegression(unittest.TestCase):
    def launch(self, code, timeout=2):
        session = mod.Session()
        turn = mod.Turn()
        session.turns.append(turn)
        session.status = "in_progress"
        proc = subprocess.Popen([sys.executable, "-u", "-c", code], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, start_new_session=True)
        monitor = mod.TurnMonitor(proc, session, turn, timeout)
        proc._turn_monitor = monitor
        session._process = proc
        monitor.start()
        self.addCleanup(mod._kill_process, proc)
        return proc, session, turn

    def test_silent_stdout_timeout_reaps_process(self):
        started = time.monotonic()
        proc, session, turn = self.launch("import time; time.sleep(60)", 0.2)
        events = list(mod.iter_codex_events(proc))
        self.assertLess(time.monotonic() - started, 2)
        self.assertIsNotNone(proc.poll())
        self.assertEqual(turn.status, "failed")
        self.assertIn("timeout", json.dumps(events))
        self.assertIsNone(session._process)

    def test_busy_stdout_cannot_postpone_deadline(self):
        started = time.monotonic()
        code = ("import json,time; "
                "[print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':str(i)}}), flush=True) for i in range(4000)]; "
                "time.sleep(60)")
        proc, session, turn = self.launch(code, 0.1)
        events = list(mod.iter_codex_events(proc))
        self.assertLess(time.monotonic() - started, 1.0)
        self.assertEqual(turn.status, "failed")
        self.assertIn("timeout", json.dumps(events))
        self.assertIsNotNone(proc.poll())
        self.assertLessEqual(len(session.items), mod.MAX_EVENTS)
        self.assertLessEqual(session.items.byte_size, mod.MAX_REPLAY_BYTES)

    def test_stderr_flood_is_drained(self):
        proc, session, turn = self.launch(
            "import sys; sys.stderr.write('x'*5000000); sys.stderr.flush(); "
            "print('{\"type\":\"turn.completed\",\"usage\":{\"input_tokens\":7}}')"
        )
        events = list(mod.iter_codex_events(proc))
        self.assertEqual(turn.status, "completed")
        self.assertEqual(session.usage["input_tokens"], 7)
        self.assertTrue(any(e["type"] == "turn.completed" for e in events))

    def test_secret_stderr_and_event_redaction(self):
        secret = "synthetic-canary-secret-0123456789"
        with patch.dict(os.environ, {"REGRESSION_API_KEY": secret}):
            proc, session, turn = self.launch(
                "import json,sys; print(json.dumps({'type':'item.completed','item':{'text':" + repr(secret) + "," + repr(secret) + ":'synthetic-object-key'}})); "
                "sys.stderr.write(" + repr(secret) + "); sys.exit(7)"
            )
            events = list(mod.iter_codex_events(proc))
        self.assertEqual(turn.status, "failed")
        self.assertNotIn(secret, json.dumps(events + session.items))
        self.assertIn("[REDACTED]", json.dumps(events))

    def test_request_mcp_header_is_redacted_from_stdout_and_stderr(self):
        secret = "synthetic-request-header-0123456789"
        session = mod.Session(tools=[{"type": "mcp", "headers": {"X-Api-Key": secret}}])
        turn = mod.Turn()
        session.turns.append(turn)
        code = "import json,sys; print(json.dumps({'type':'item.completed','item':{'text':" + repr(secret) + "," + repr(secret) + ":'synthetic-object-key'}})); sys.stderr.write(" + repr(secret) + "); sys.exit(7)"
        proc = subprocess.Popen([sys.executable, "-u", "-c", code], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, start_new_session=True)
        monitor = mod.TurnMonitor(proc, session, turn, 2)
        proc._turn_monitor = monitor
        self.addCleanup(mod._kill_process, proc)
        monitor.start()
        events = list(mod.iter_codex_events(proc))
        self.assertNotIn(secret, json.dumps(events + session.items))
        self.assertIn("[REDACTED]", json.dumps(events))

    def test_completion_then_nonzero_exit_is_failure_without_success_event(self):
        proc, _, turn = self.launch("import sys; print('{\"type\":\"turn.completed\"}'); sys.exit(7)")
        events = list(mod.iter_codex_events(proc))
        self.assertEqual(turn.status, "failed")
        self.assertFalse(any(event.get("type") == "turn.completed" for event in events))

    def test_final_jsonl_record_without_newline_is_preserved(self):
        proc, _, turn = self.launch("import sys; sys.stdout.write('{\"type\":\"turn.completed\"}')")
        events = list(mod.iter_codex_events(proc))
        self.assertEqual(turn.status, "completed")
        self.assertEqual(events[-1]["type"], "turn.completed")

    def test_timeout_kills_tool_child(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "pid"
            code = ("import subprocess,time; from pathlib import Path; "
                    "p=subprocess.Popen(['sleep','60']); Path(" + repr(str(marker)) + ").write_text(str(p.pid)); time.sleep(60)")
            proc, _, _ = self.launch(code, 0.4)
            list(mod.iter_codex_events(proc))
            pid = int(marker.read_text())
            status = Path(f"/proc/{pid}/stat")
            # An orphan may briefly remain a zombie until container PID 1 reaps it;
            # it must not remain a running tool process.
            self.assertTrue(not status.exists() or status.read_text().split()[2] == "Z")

    def test_background_deadline_runs_without_reader(self):
        proc, session, turn = self.launch("import time; time.sleep(60)", 0.2)
        proc._turn_monitor.thread.join(2)
        self.assertFalse(proc._turn_monitor.thread.is_alive())
        self.assertEqual(turn.status, "failed")
        self.assertIsNone(session._process)

    def test_subscribers_do_not_steal_or_duplicate_usage(self):
        proc, session, turn = self.launch("print('{\"type\":\"turn.completed\",\"usage\":{\"input_tokens\":7}}')")
        first = list(mod.iter_codex_events(proc))
        second = list(mod.iter_codex_events(proc))
        self.assertEqual(first, second)
        self.assertEqual(session.usage["input_tokens"], 7)

    def test_oversize_unterminated_line_is_bounded_failure(self):
        proc, _, turn = self.launch("import sys,time; sys.stdout.write('x'*400000); sys.stdout.flush(); time.sleep(60)")
        events = list(mod.iter_codex_events(proc))
        self.assertEqual(turn.status, "failed")
        self.assertIn("exceeds", json.dumps(events))

    def test_failed_upstream_event_is_failure_even_zero_exit(self):
        proc, _, turn = self.launch("print('{\"type\":\"turn.failed\",\"error\":{\"message\":\"upstream failure\"}}')")
        list(mod.iter_codex_events(proc))
        self.assertEqual(turn.status, "failed")

    def test_zero_exit_without_completion_is_failure(self):
        proc, _, turn = self.launch("print('{}')")
        self.assertIn("without turn.completed", json.dumps(list(mod.iter_codex_events(proc))))
        self.assertEqual(turn.status, "failed")

    def test_replay_buffer_bounds_bytes(self):
        proc, _, turn = self.launch(
            "import json; [print(json.dumps({'type':'message.delta','delta':'a'*10000})) for _ in range(250)]; "
            "print('{\"type\":\"turn.completed\"}')"
        )
        proc._turn_monitor.thread.join(4)
        events = list(mod.iter_codex_events(proc))
        self.assertEqual(turn.status, "completed")
        self.assertLessEqual(proc._turn_monitor.buffer_bytes, mod.MAX_REPLAY_BYTES)
        self.assertEqual(events[0]["type"], "events.truncated")


class AdapterRegression(unittest.TestCase):
    def test_saved_agent_capacity(self):
        saved = mod.AgentStore()
        with patch.object(mod, "MAX_AGENTS", 1):
            saved.create("test")
            with self.assertRaises(mod.CapacityError):
                saved.create("second")

    def test_request_parameters(self):
        self.assertTrue(mod._validate_body({"stream": "true"}))
        self.assertTrue(mod._validate_body({"background": True, "stream": True}))
        self.assertTrue(mod._validate_body({"agent": {"tools": [{"type": "function"}]}}))
        self.assertFalse(mod._validate_body({"background": True, "agent": {"model": "test"}}))

    def test_symlink_artifact_escape_and_secret_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(mod, "WORKSPACE", tmp):
                Path(tmp, "outside").symlink_to("/tmp")
                self.assertIsNone(mod._resolve_artifact_path("outside/no-read"))
                self.assertIsNone(mod._resolve_artifact_path(".env"))
                Path(tmp, ".env").write_text("synthetic-secret-fixture\n")
                Path(tmp, "public.log").symlink_to(Path(tmp, ".env"))
                self.assertIsNone(mod._resolve_artifact_path("public.log"))
                self.assertIsNone(mod._resolve_artifact_path("sub/.aws/config"))

    def test_mcp_headers_are_redacted_in_public_config(self):
        config = mod.AgentConfig(name="synthetic-header", metadata={"note":"synthetic-header"}, tools=[{"type": "mcp", "headers": {"X-Key": "synthetic-header"}}])
        self.assertNotIn("synthetic-header", json.dumps(config.to_dict()))
        self.assertEqual(config.tools[0]["headers"]["X-Key"], "synthetic-header")

    def test_first_turn_argv_uses_exec_not_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(mod, "WORKSPACE", tmp), patch.object(mod.subprocess, "Popen") as popen, patch.object(mod.TurnMonitor, "start"):
                session = mod.Session(model="test", instructions="Only say hello")
                session.turns.append(mod.Turn())
                mod.spawn_codex_turn(session, "--a prompt")
                argv = popen.call_args.args[0]
                self.assertEqual(argv[:3], ["codex", "exec", "--json"])
                self.assertNotIn("resume", argv)
                self.assertEqual(argv[-2:], ["--", "--a prompt"])
                self.assertIn('developer_instructions="Only say hello"', argv)
                session.turns.append(mod.Turn())
                session.thread_id = "specific-thread"
                mod.spawn_codex_turn(session, "Continue")
                self.assertEqual(popen.call_args.args[0][-4:], ["resume", "specific-thread", "--", "Continue"])


if __name__ == "__main__":
    unittest.main()
