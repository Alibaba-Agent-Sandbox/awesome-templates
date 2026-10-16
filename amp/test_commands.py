"""Configuration ownership, permission and subprocess privacy regressions."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback

import pytest

SPEC = importlib.util.spec_from_file_location("amp_template_commands", Path(__file__).with_name("commands.py"))
commands = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(commands)


@pytest.mark.parametrize("existing", [False, True])
def test_setup_preserves_settings_and_permissions(monkeypatch, tmp_path, existing):
    settings = tmp_path / "new-directory" / "settings.json"
    if existing:
        settings.parent.mkdir()
        settings.write_text('{"amp.dangerouslyAllowAll":false,"custom":"preserved"}\n')
        settings.chmod(0o640)
    monkeypatch.setenv("AMP_SETTINGS_FILE", str(settings))
    monkeypatch.setattr(commands.shutil, "which", lambda _: None)
    before = settings.read_bytes() if existing else None
    result = commands.amp_setup_check()
    assert result["settings_exists"] is existing
    assert result["dangerously_allow_all"] is False
    if existing:
        assert settings.read_bytes() == before
        assert settings.stat().st_mode & 0o777 == 0o640
    else:
        assert not settings.parent.exists()


def test_version_inspection_does_not_create_config(monkeypatch, tmp_path):
    settings = tmp_path / "settings.json"
    monkeypatch.setenv("AMP_SETTINGS_FILE", str(settings))
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    # This is a real subprocess, with the version argument interpreted by Python.
    monkeypatch.setattr(commands, "_amp_executable", lambda: sys.executable)
    result = commands._run_amp(["-c", "print('version-fixture')"], timeout=5)
    assert result.stdout.strip() == "version-fixture"
    assert not settings.exists()


def test_missing_key_never_starts_login(monkeypatch):
    monkeypatch.delenv("AMP_API_KEY", raising=False)
    monkeypatch.setattr(commands, "_run_amp", lambda *a, **k: pytest.fail("must not start device login"))
    with pytest.raises(RuntimeError, match="AMP_API_KEY is required"):
        commands.amp_execute("test")


@pytest.mark.parametrize("allow", [False, True])
def test_execute_requires_explicit_permission_override(monkeypatch, allow):
    captured = []
    monkeypatch.setenv("AMP_API_KEY", "synthetic-test-key")
    def run(args, timeout):
        captured.extend(args)
        return subprocess.CompletedProcess(args, 0, "ok", "")
    monkeypatch.setattr(commands, "_run_amp", run)
    assert commands.amp_execute("edit a file", dangerously_allow_all=allow) == "ok"
    assert ("--dangerously-allow-all" in captured) is allow


@pytest.mark.parametrize("exit_code", [0, 2])
def test_secrets_redacted_in_success_and_error(monkeypatch, exit_code):
    key = 'synthetic-"quoted"-key'
    monkeypatch.setenv("AMP_API_KEY", key)
    monkeypatch.setenv("ABX_SERVER_TOKEN", "synthetic-server-token")
    output = json.dumps({"text": key + " synthetic-server-token"})
    monkeypatch.setattr(commands, "_run_amp", lambda args, timeout: subprocess.CompletedProcess(args, exit_code, output, output))
    if exit_code:
        with pytest.raises(RuntimeError) as exc:
            commands.amp_execute("test")
        result = str(exc.value)
    else:
        result = commands.amp_execute("test")
    assert key not in result
    assert json.dumps(key)[1:-1] not in result
    assert "synthetic-server-token" not in result
    assert "[REDACTED]" in result


def test_timeout_kills_owned_descendant_and_hides_prompt(monkeypatch, tmp_path):
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    monkeypatch.setattr(commands, "_amp_executable", lambda: sys.executable)
    marker = tmp_path / "escaped-child"
    private_prompt = "synthetic-private-prompt"
    child = f"import time;time.sleep(2);open({str(marker)!r},'w').write('bad')"
    parent = "import subprocess,sys,time;subprocess.Popen([sys.executable,'-c'," + repr(child) + "]);time.sleep(30)"
    with pytest.raises(RuntimeError, match="timed out") as exc:
        commands._run_amp(["-c", parent, private_prompt], timeout=1)
    assert private_prompt not in "".join(traceback.format_exception(exc.value))
    time.sleep(1.2)
    assert not marker.exists()


@pytest.mark.parametrize("exit_code", [0, 7])
def test_completed_leader_stops_owned_children_with_redirected_stdio(tmp_path, exit_code):
    """A successful/error parent exit must never leave its owned worker running."""
    marker = tmp_path / "escaped-completion"
    ready = tmp_path / "child-ready"
    child = ("import time;from pathlib import Path;"
             f"Path({str(ready)!r}).write_text('ready');"
             f"time.sleep(1.3);Path({str(marker)!r}).write_text('bad')")
    leader = ("import subprocess,sys,time;from pathlib import Path;"
              "subprocess.Popen([sys.executable,'-c'," + repr(child) +
              "],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);"
              f"ready=Path({str(ready)!r});"
              "deadline=time.monotonic()+3\n"
              "while not ready.exists() and time.monotonic()<deadline:time.sleep(.01)\n"
              "print('leader-output',flush=True);sys.exit(" + str(exit_code) + ")")
    code, stdout, stderr = commands._run_process([sys.executable, "-c", leader], cwd=str(tmp_path), timeout=5)
    assert ready.exists()
    assert code == exit_code and stdout == "leader-output\n" and stderr == ""
    time.sleep(1.5)
    assert not marker.exists()


def test_deadline_leader_exit_cannot_orphan_term_ignoring_child(tmp_path):
    marker = tmp_path / "escaped-timeout"
    ready = tmp_path / "ignoring-child-ready"
    child = ("import signal,time;from pathlib import Path;"
             "signal.signal(signal.SIGTERM,signal.SIG_IGN);"
             f"Path({str(ready)!r}).write_text('ready');"
             f"time.sleep(2);Path({str(marker)!r}).write_text('bad');time.sleep(30)")
    leader = ("import subprocess,sys,time;subprocess.Popen([sys.executable,'-c'," + repr(child) +
              "],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(30)")
    with pytest.raises(RuntimeError, match="timed out"):
        commands._run_process([sys.executable, "-c", leader], cwd=str(tmp_path), timeout=1)
    assert ready.exists()
    time.sleep(1.2)
    assert not marker.exists()


def test_owned_runner_drains_both_large_pipes_before_return(tmp_path):
    code, stdout, stderr = commands._run_process([sys.executable, "-c",
        "import sys;sys.stdout.write('x'*200000);sys.stderr.write('y'*200000)"], cwd=str(tmp_path), timeout=5)
    assert code == 0 and stdout == "x"*200000 and stderr == "y"*200000
