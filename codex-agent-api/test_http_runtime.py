"""Real local HTTP/process integration using an explicit deterministic CLI fixture.

This regression suite does not certify Codex/model/provider execution. It tests
background routing, cancellation and SSE against actual server/child processes.
"""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest

import httpx


class HTTPRuntime(unittest.TestCase):
    def test_background_completion_and_active_session_cancellation(self):
        template = Path(__file__).with_name("commands.py").resolve()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cli = root / "codex"
            cli.write_text("#!/usr/bin/env python3\n" + '''import json, os, sys, time
from pathlib import Path
Path(os.environ['FIXTURE_PID']).write_text(str(os.getpid()))
Path(os.environ['FIXTURE_ARGV']).write_text(json.dumps(sys.argv))
print(json.dumps({'type':'thread.started','thread_id':'fixture-thread'}), flush=True)
if sys.argv[-1] == 'wait':
    time.sleep(60)
else:
    time.sleep(0.2)
    print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'fixture-only'}}), flush=True)
    print(json.dumps({'type':'turn.completed','usage':{'input_tokens':7,'output_tokens':3}}), flush=True)
''')
            cli.chmod(0o700)
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
            env = {key: value for key, value in os.environ.items()
                   if not any(label in key.upper() for label in ("KEY", "SECRET", "TOKEN", "PASSWORD", "CREDENTIAL"))}
            env.update(PATH=str(root) + os.pathsep + env.get("PATH", ""),
                       WORKSPACE=str(root), CODEX_HOME=str(root / "codex-home"),
                       FIXTURE_PID=str(root / "fixture.pid"), FIXTURE_ARGV=str(root / "fixture.argv"))
            proc = subprocess.Popen([sys.executable, "-m", "agent_sandbox.server", "serve", "--port", str(port),
                                     "--commands", str(template)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=3) as client:
                    deadline = time.monotonic() + 10
                    while True:
                        try:
                            response = client.get("/health")
                            if response.status_code == 200:
                                break
                        except httpx.HTTPError:
                            pass
                        if proc.poll() is not None or time.monotonic() > deadline:
                            self.fail("Fixture server failed to start")
                        time.sleep(0.05)
                    secret = "synthetic-request-only-header"
                    agent = client.post("/v1/agents", json={"name": secret, "metadata": {"note": secret},
                        "tools": [{"type": "mcp", "server_url": "http://localhost/fixture-unused", "headers": {"X-Api-Key": secret}}]})
                    self.assertEqual(agent.status_code, 200)
                    self.assertNotIn(secret, agent.text)
                    response = client.post("/v1/agents/sessions", json={"agent": agent.json()["id"], "input": "complete", "background": True})
                    self.assertEqual(response.status_code, 200)
                    session = response.json()
                    self.assertEqual(session["status"], "in_progress")
                    sid = session["id"]
                    deadline = time.monotonic() + 3
                    while time.monotonic() < deadline:
                        session = client.get(f"/v1/agents/sessions/{sid}").json()
                        if session["status"] != "in_progress":
                            break
                        time.sleep(0.025)
                    self.assertEqual(session["status"], "idle")
                    self.assertEqual(session["usage"]["input_tokens"], 7)
                    # Execution uses the actual header, while public responses mask it.
                    self.assertIn(secret, (root / "fixture.argv").read_text())
                    (root / "public.log").write_text(secret)
                    response = client.get(f"/v1/agents/sessions/{sid}/artifacts/cHVibGljLmxvZw")
                    self.assertEqual(response.status_code, 200)
                    self.assertNotIn(secret, response.text)
                    self.assertIn("REDACTED", response.text)
                    self.assertTrue(client.delete(f"/v1/agents/sessions/{sid}/artifacts/cHVibGljLmxvZw").json()["deleted"])
                    response = client.post(f"/v1/agents/sessions/{sid}/events", json={"input": "complete", "stream": True})
                    self.assertIn("agent.session.turn.completed", response.text)
                    self.assertNotIn("turn.failed", response.text)
                    self.assertEqual(client.get(f"/v1/agents/sessions/{sid}").json()["usage"]["input_tokens"], 14)
                    response = client.post(f"/v1/agents/sessions/{sid}/events", json={"input": "wait", "background": True})
                    self.assertEqual(response.json()["status"], "in_progress")
                    self.assertEqual(client.post(f"/v1/agents/sessions/{sid}/events", json={"input": "conflict"}).status_code, 409)
                    time.sleep(0.05)
                    pid = int((root / "fixture.pid").read_text())
                    self.assertTrue(client.delete(f"/v1/agents/sessions/{sid}").json()["deleted"])
                    deadline = time.monotonic() + 2
                    while Path(f"/proc/{pid}").exists() and time.monotonic() < deadline:
                        time.sleep(0.025)
                    self.assertFalse(Path(f"/proc/{pid}").exists())
                    self.assertEqual(client.get(f"/v1/agents/sessions/{sid}").status_code, 404)
            finally:
                proc.terminate()
                try:
                    proc.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.communicate(timeout=2)


if __name__ == "__main__":
    unittest.main()
