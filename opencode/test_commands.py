"""Regression checks for argument boundaries, sensitive output and read-only setup."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess

import pytest

SPEC = importlib.util.spec_from_file_location("opencode_template_commands", Path(__file__).with_name("commands.py"))
commands = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(commands)


def test_run_keeps_option_shaped_prompt_positional(monkeypatch, tmp_path):
    captured = {}
    monkeypatch.setattr(commands, "_child_config", lambda model: ("/synthetic/config.json", None))
    def run(argv, **kwargs):
        captured["argv"] = argv
        return subprocess.CompletedProcess(argv, 0, json.dumps({"type": "text", "sessionID": "ses_test", "part": {"text": "done"}}) + "\n", "")
    monkeypatch.setattr(commands, "_run", run)
    result = commands._execute_run("--command something; $(false)", "dashscope/test", "", "", False, str(tmp_path))
    assert captured["argv"][-2:] == ["--", "--command something; $(false)"]
    assert result["text"] == "done"
    assert result["session_id"] == "ses_test"


def test_cli_error_never_returns_prompt_or_output():
    result = subprocess.CompletedProcess(["opencode"], 2, "arbitrary-private-prompt", "synthetic-api-secret")
    with pytest.raises(RuntimeError) as exc:
        commands._require_ok(result, "opencode run")
    assert str(exc.value) == "opencode run exited 2; CLI output omitted"


def test_success_events_redact_short_and_json_escaped_secrets(monkeypatch):
    secret = 'synthetic-"quote"-credential'
    monkeypatch.setenv("SYNTHETIC_CREDENTIAL", secret)
    monkeypatch.setenv("SYNTHETIC_TOKEN", "abcd")
    raw = json.dumps({"type": "text", "part": {"text": secret + " abcd"}}) + "\n"
    safe = commands._safe_events(raw)
    assert json.loads(safe)["part"]["text"] == "*** ***"
    assert secret not in commands._parse_events(safe)[0]


def test_setup_does_not_create_or_rewrite_config(monkeypatch, tmp_path):
    config = tmp_path / "opencode.json"
    original = commands.MODULE_CONFIG.read_bytes()
    config.write_bytes(original)
    monkeypatch.setenv("OPENCODE_CONFIG", str(config))
    def run(argv, **kwargs):
        assert argv == ["opencode", "--version"]
        return subprocess.CompletedProcess(argv, 0, commands.PINNED_VERSION + "\n", "")
    monkeypatch.setattr(commands, "_run", run)
    monkeypatch.setattr(commands, "_child_config", lambda *args: pytest.fail("setup must not generate config"))
    monkeypatch.setattr(commands.subprocess, "Popen", lambda *args, **kwargs: pytest.fail("setup must not start a service"))
    assert commands.opencode_setup_check() == "ok"
    assert config.read_bytes() == original
    assert list(tmp_path.iterdir()) == [config]


def test_module_config_is_available_without_image_path_access(monkeypatch):
    monkeypatch.delenv("OPENCODE_CONFIG", raising=False)
    monkeypatch.setattr(commands, "IMAGE_CONFIG", Path("/unavailable/nontraversable/opencode.json"))
    assert commands._config_file() == commands.MODULE_CONFIG


def test_conflicting_session_options_fail_before_cli(monkeypatch):
    monkeypatch.setattr(commands, "_run", lambda *a, **k: pytest.fail("must not execute CLI"))
    with pytest.raises(ValueError, match="mutually exclusive"):
        commands._execute_run("test", "", "", "ses_test", True, "")


@pytest.mark.parametrize("model,agent,session", [
    ("--print-logs", "", ""), ("dashscope/test", "--print-logs", ""),
    ("dashscope/test", "", "--print-logs"),
])
def test_option_shaped_selectors_fail_before_cli(monkeypatch, model, agent, session):
    monkeypatch.setattr(commands, "_run", lambda *a, **k: pytest.fail("must not execute CLI"))
    with pytest.raises(ValueError, match="option prefix"):
        commands._execute_run("test", model, agent, session, False, "")


def test_timeout_traceback_never_discloses_prompt(monkeypatch, tmp_path):
    import traceback
    secret_prompt = "synthetic-private-timeout-prompt"
    def timeout(argv, **kwargs):
        raise subprocess.TimeoutExpired(argv, 1, output="private stdout", stderr="private stderr")
    monkeypatch.setattr(commands.subprocess, "run", timeout)
    with pytest.raises(RuntimeError) as exc:
        commands._run(["opencode", "run", secret_prompt], cwd=str(tmp_path), timeout=1)
    formatted = "".join(traceback.format_exception(exc.value))
    assert secret_prompt not in formatted
    assert "private stdout" not in formatted
    assert exc.value.__suppress_context__ is True
    assert exc.value.__cause__ is None


def test_stale_pid_file_cannot_signal_unrelated_child(monkeypatch, tmp_path):
    import os
    import sys
    unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"],
                                 start_new_session=True)
    legacy_state = tmp_path / "opencode-serve.json"
    legacy_state.write_text(json.dumps({"pid": unrelated.pid, "port": 4096, "hostname": "0.0.0.0"}))
    # This injects the old path for regression: reverting to file-based authority
    # would kill this unrelated child. The current lifecycle never reads it.
    monkeypatch.setattr(commands, "STATE_PATH", legacy_state, raising=False)
    monkeypatch.setattr(commands, "_SERVE_PROCESS", None)
    monkeypatch.setattr(commands, "_SERVE_OWNER_PID", 0)
    try:
        assert commands.opencode_serve_status()["running"] is False
        assert commands.opencode_serve_stop() == "stopped"
        assert unrelated.poll() is None
        assert json.loads(legacy_state.read_text())["pid"] == unrelated.pid
    finally:
        unrelated.terminate()
        unrelated.wait(timeout=5)


def test_nonmatching_interpreter_ownership_refuses_signal(monkeypatch):
    import os
    import sys
    unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"],
                                 start_new_session=True)
    monkeypatch.setattr(commands, "_SERVE_PROCESS", unrelated)
    monkeypatch.setattr(commands, "_SERVE_OWNER_PID", os.getpid() + 1)
    try:
        assert commands.opencode_serve_status()["running"] is False
        with pytest.raises(RuntimeError, match="signal refused"):
            commands.opencode_serve_stop()
        assert unrelated.poll() is None
    finally:
        unrelated.terminate()
        unrelated.wait(timeout=5)


def test_concurrent_start_owns_one_child_and_stop_reaps_it(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    import os
    import sys
    import threading
    original_popen = subprocess.Popen
    spawned = []
    barrier = threading.Barrier(4)
    monkeypatch.setattr(commands, "_SERVE_PROCESS", None)
    monkeypatch.setattr(commands, "_SERVE_OWNER_PID", 0)
    monkeypatch.setattr(commands, "_healthy", lambda port: True)
    def start_child(argv, **kwargs):
        proc = original_popen([sys.executable, "-c", "import time; time.sleep(30)"],
                              start_new_session=True)
        spawned.append(proc)
        return proc
    monkeypatch.setattr(commands.subprocess, "Popen", start_child)
    def start_one(index):
        barrier.wait(timeout=5)
        return commands.opencode_serve_start(port=4096, hostname="127.0.0.1")
    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            states = list(pool.map(start_one, range(4)))
        assert len(spawned) == 1
        assert {state["pid"] for state in states} == {spawned[0].pid}
        assert all(state["running"] for state in states)
        with pytest.raises(RuntimeError, match="different bind settings"):
            commands.opencode_serve_start(port=4096, hostname="0.0.0.0")
        assert commands.opencode_serve_stop() == "stopped"
        assert spawned[0].returncode is not None
        assert commands.opencode_serve_status()["running"] is False
    finally:
        commands._stop_serve()
        for proc in spawned:
            if proc.poll() is None:
                proc.terminate()
            proc.wait(timeout=5)


def test_mismatching_process_group_refuses_signal(monkeypatch):
    import os
    import sys
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"],
                             start_new_session=True)
    monkeypatch.setattr(commands, "_SERVE_PROCESS", child)
    monkeypatch.setattr(commands, "_SERVE_OWNER_PID", os.getpid())
    original_kill = os.kill
    try:
        with monkeypatch.context() as group_patch:
            group_patch.setattr(commands.os, "getpgid", lambda pid: pid + 1)
            group_patch.setattr(commands.os, "killpg", lambda *a: pytest.fail("mismatched group must not receive signal"))
            with pytest.raises(RuntimeError, match="identity mismatch; signal refused"):
                commands.opencode_serve_stop()
            assert child.poll() is None
    finally:
        original_kill(child.pid, 15)
        child.wait(timeout=5)
