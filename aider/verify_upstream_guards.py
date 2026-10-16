"""Actual installed Aider CLI with a deterministic loopback model, not L3 proof.

Run only in a fresh dedicated sandbox. HOME is preserved; no native profile is
created or removed. The commands module's normal native-home refusal still runs.
"""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading


def edit_response(path: str) -> str:
    """A real multiline whole-file response understood by official Aider."""
    return f"{path}\n```\nUNSELECTED\n```"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commands", type=Path, default=Path(__file__).with_name("commands.py"))
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("aider_guard_commands", args.commands)
    commands = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(commands)
    responses = []
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            calls.append(payload)
            answer = responses.pop(0) if responses else "No additional changes."
            data = json.dumps({"id": "guard-fixture", "object": "chat.completion", "created": 1,
                "model": "synthetic", "choices": [{"index": 0, "message": {
                "role": "assistant", "content": answer}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30}}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    os.environ.update(AIDER_API_KEY="synthetic-loopback-key",
        AIDER_BASE_URL=f"http://127.0.0.1:{server.server_port}/v1", AIDER_MODEL="synthetic")
    try:
        with tempfile.TemporaryDirectory(prefix="aider-upstream-guard-") as directory:
            root = Path(directory)
            project = root / "project"
            project.mkdir()
            subprocess.run(["git", "init", "--quiet", str(project)], check=True)
            os.environ["WORKSPACE"] = str(project)
            selected = project / "selected.py"
            selected.write_text("original\n")
            responses.append(edit_response("selected.py"))
            before = len(calls)
            result = commands.aider("Edit only selected.py.", files='["selected.py"]',
                allow_write=True, command_timeout=40)
            assert len(calls) > before, "selected edit fixture did not reach model"
            assert result["changed_files"] == ["selected.py"], "selected edit was not applied"
            assert selected.read_text() == "UNSELECTED\n", "whole-file fixture did not edit selected content"
            selected.write_text("original\n")
            print("PASS actual Aider CLI applies explicit selected whole-file edit", flush=True)
            for prefix in ("/run ", "!"):
                marker = root / ("slash-marker" if prefix.startswith("/") else "bang-marker")
                responses.append("Literal request received; no command executed.")
                before = len(calls)
                commands.aider(prefix + "touch " + str(marker), files='["selected.py"]', command_timeout=40)
                assert len(calls) > before, "prompt bypassed model as a command"
                assert not marker.exists(), "prompt command executed"
            print("PASS actual Aider CLI slash/bang requests remain literal model text", flush=True)
            existing = root / "existing-private.txt"
            existing.write_text("UNCHANGED_PRIVATE_FIXTURE\n")
            paths = (str(root / "absolute-escape" / "created.txt"),
                "../../" + root.name + "/relative-escape/created.txt", str(existing))
            for escape in paths:
                before = len(calls)
                response = edit_response(escape)
                assert response.splitlines() == [escape, "```", "UNSELECTED", "```"], "invalid multiline edit fixture"
                responses.append(response)
                result = commands.aider("Change only the selected file.", files='["selected.py"]',
                    allow_write=True, command_timeout=40)
                assert len(calls) > before, "unselected-path fixture did not reach model"
                assert not (root / "absolute-escape").exists(), "absolute unselected artifact created"
                assert not (root / "relative-escape").exists(), "relative unselected artifact created"
                assert existing.read_text() == "UNCHANGED_PRIVATE_FIXTURE\n", "unselected existing file changed"
                assert result["changed_files"] == [], "unselected model response changed selected files"
                assert "Skipping edits to" in result["stdout"] + result["stderr"], "upstream did not reject unselected path"
            assert selected.read_text() == "original\n", "selected source changed unexpectedly"
            print("PASS actual Aider CLI rejects unselected absolute/relative creation and existing edits", flush=True)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == "__main__":
    main()
