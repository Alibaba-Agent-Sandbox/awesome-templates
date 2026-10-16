"""Runtime regressions: working directory, argv, credentials and process cleanup."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import time
import traceback

import pytest

spec = importlib.util.spec_from_file_location("droid_commands", Path(__file__).with_name("commands.py"))
commands = importlib.util.module_from_spec(spec)
spec.loader.exec_module(commands)


def test_missing_key_never_starts_cli(monkeypatch, tmp_path):
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    monkeypatch.delenv("FACTORY_API_KEY", raising=False)
    monkeypatch.setattr(commands, "_run", lambda *a: pytest.fail("must not start login"))
    with pytest.raises(RuntimeError, match="FACTORY_API_KEY is required"):
        commands.droid("do something")


@pytest.mark.parametrize("auto", ["", "low", "medium", "high"])
def test_workspace_and_prompt_are_literal(monkeypatch, tmp_path, auto):
    root = tmp_path / "workspace"
    project = root / "project"
    project.mkdir(parents=True)
    monkeypatch.setenv("WORKSPACE", str(root))
    monkeypatch.setenv("FACTORY_API_KEY", "synthetic-key")
    prompt = "--help ; $(touch injected)"
    calls = []
    monkeypatch.setattr(commands, "_run", lambda *args: calls.append(args) or "ok")
    assert commands.droid(prompt, auto=auto, cwd="project", command_timeout=12) == "ok"
    argv, cwd, timeout = calls[0]
    assert argv == ["exec", *(["--auto", auto] if auto else []), "--", prompt]
    assert cwd == project and timeout == 12


def test_workspace_escape_and_symlink_escape_rejected(monkeypatch, tmp_path):
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "link").symlink_to(outside, target_is_directory=True)
    monkeypatch.setenv("WORKSPACE", str(root))
    for cwd in ("../outside", "link", str(outside)):
        with pytest.raises(ValueError, match="inside WORKSPACE"):
            commands._workdir(cwd)


@pytest.mark.parametrize("kwargs", [{"prompt": " "}, {"prompt": "x", "auto": "unsafe"},
    {"prompt": "x", "command_timeout": 0}, {"prompt": "x", "command_timeout": 601},
    {"prompt": "x", "command_timeout": True}, {"prompt": "x", "command_timeout": 1.5}])
def test_invalid_values_do_not_launch(monkeypatch, kwargs):
    monkeypatch.setattr(commands, "_run", lambda *a: pytest.fail("must not execute"))
    with pytest.raises(ValueError):
        commands.droid(**kwargs)


@pytest.mark.parametrize("exit_code", [0, 2])
def test_success_and_error_redact_raw_and_json_secrets(monkeypatch, tmp_path, exit_code):
    secret = 'synthetic-"quoted"-key'
    monkeypatch.setenv("FACTORY_API_KEY", secret)
    monkeypatch.setenv("ABX_SERVER_TOKEN", "synthetic-server-token")
    monkeypatch.setattr(commands, "_executable", lambda: sys.executable)
    raw = secret + " synthetic-server-token " + json.dumps(secret)
    code = f"import sys;print({raw!r});sys.exit({exit_code})"
    if exit_code:
        with pytest.raises(RuntimeError) as caught:
            commands._run(["-c", code], tmp_path, 5)
        text = str(caught.value)
    else:
        text = commands._run(["-c", code], tmp_path, 5)
    assert secret not in text and json.dumps(secret)[1:-1] not in text
    assert "synthetic-server-token" not in text and "[REDACTED]" in text


def test_timeout_kills_owned_descendant_and_hides_prompt(monkeypatch, tmp_path):
    monkeypatch.setattr(commands, "_executable", lambda: sys.executable)
    marker = tmp_path / "orphan-created"
    private = "synthetic-private-prompt"
    child = f"import time;time.sleep(2);open({str(marker)!r},'w').write('bad')"
    parent = "import subprocess,sys,time;subprocess.Popen([sys.executable,'-c'," + repr(child) + "]);time.sleep(30)"
    with pytest.raises(RuntimeError, match="timed out") as caught:
        commands._run(["-c", parent, private], tmp_path, 1)
    assert private not in "".join(traceback.format_exception(caught.value))
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
