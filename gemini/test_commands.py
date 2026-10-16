"""Behavior regressions for Gemini permissions, diagnostics and cancellation."""
import importlib.util
import json
from pathlib import Path
import sys
import time
import traceback

import pytest

SPEC = importlib.util.spec_from_file_location("gemini_template_commands", Path(__file__).with_name("commands.py"))
commands = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(commands)


def test_setup_does_not_create_rewrite_or_disclose_settings(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    monkeypatch.setattr(commands.shutil, "which", lambda name: None)
    result = commands.gemini_setup_check()
    assert not result["installed"] and not (tmp_path / ".gemini").exists()
    settings = tmp_path / ".gemini" / "settings.json"
    settings.parent.mkdir()
    original = '{"private":"synthetic-settings-secret","custom":true}\n'
    settings.write_text(original)
    settings.chmod(0o640)
    result = commands.gemini_setup_check()
    assert settings.read_text() == original and settings.stat().st_mode & 0o777 == 0o640
    assert "synthetic-settings-secret" not in json.dumps(result)
    settings.write_text("invalid json")
    assert not commands.gemini_setup_check()["settings"][0]["valid_json_object"]


def test_missing_key_never_launches_cli_or_uses_openai_key(monkeypatch, tmp_path):
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-unrelated-key")
    monkeypatch.setattr(commands, "_run", lambda *a, **k: pytest.fail("no OAuth or model invocation"))
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY is required"):
        commands.gemini("test")


@pytest.mark.parametrize("yolo", [True, False])
def test_verified_headless_flags_and_optin_permissions(monkeypatch, tmp_path, yolo):
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-gemini-key")
    monkeypatch.setattr(commands, "_executable", lambda: "gemini")
    captured = {}
    def run(argv, **kwargs):
        captured.update(argv=argv, **kwargs)
        return "{}"
    monkeypatch.setattr(commands, "_run", run)
    prompt = "edit 'code'; $(do-not-run)"
    commands.gemini(prompt, model="compatible-model", yolo=yolo, command_timeout=42)
    assert captured["argv"] == ["gemini", "-p", prompt, "--model", "compatible-model", "--output-format", "json", "--approval-mode", "yolo" if yolo else "plan"]
    assert captured["command_timeout"] == 42
    for kwargs in ({"command_timeout": 0}, {"command_timeout": 1801}, {"prompt": " "}):
        with pytest.raises(ValueError):
            commands.gemini(**({"prompt": "test"} | kwargs))


def test_workdir_rejects_missing_paths_traversal_and_symlink_escape(monkeypatch, tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    child = root / "project"
    child.mkdir()
    (root / "escape").symlink_to(tmp_path, target_is_directory=True)
    monkeypatch.setenv("WORKSPACE", str(root))
    assert commands._workdir("project") == str(child)
    assert commands._workdir(str(child)) == str(child)
    for path in ("../", "escape", "missing", str(tmp_path)):
        with pytest.raises(ValueError):
            commands._workdir(path)


@pytest.mark.parametrize("failed", [True, False])
def test_secret_redacted_from_success_and_failure(monkeypatch, tmp_path, failed):
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    secret = 'synthetic-"quoted"-secret'
    monkeypatch.setenv("GEMINI_API_KEY", secret)
    monkeypatch.setenv("ABX_SERVER_TOKEN", "synthetic-server-token")
    code = "import os,json,sys;print(json.dumps(dict(key=os.environ['GEMINI_API_KEY'], token=os.environ['ABX_SERVER_TOKEN'])));sys.exit(" + str(int(failed)) + ")"
    if failed:
        with pytest.raises(RuntimeError) as exc:
            commands._run([sys.executable, "-c", code], command_timeout=5)
        output = str(exc.value)
    else:
        output = commands._run([sys.executable, "-c", code], command_timeout=5)
    assert secret not in output and json.dumps(secret)[1:-1] not in output
    assert "synthetic-server-token" not in output and "[REDACTED]" in output


def test_timeout_kills_owned_descendants_and_hides_argv(monkeypatch, tmp_path):
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    marker = tmp_path / "survived"
    child = f"import time;time.sleep(2);open({str(marker)!r},'w').write('bad')"
    parent = "import subprocess,sys,time;subprocess.Popen([sys.executable,'-c'," + repr(child) + "]);time.sleep(30)"
    private_prompt = "private-prompt"
    with pytest.raises(RuntimeError, match="timed out") as exc:
        commands._run([sys.executable, "-c", parent, private_prompt], command_timeout=1)
    assert private_prompt not in "".join(traceback.format_exception(exc.value))
    time.sleep(1.2)
    assert not marker.exists()


@pytest.mark.skipif(commands.shutil.which("gemini") is None, reason="real pinned CLI not on PATH")
def test_actual_installed_cli_diagnostics_preserve_user_settings(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    settings = tmp_path / ".gemini" / "settings.json"
    settings.parent.mkdir()
    original = b'{"custom":{"enabled":true}}\n'
    settings.write_bytes(original)
    settings.chmod(0o640)
    result = commands.gemini_setup_check()
    assert result["installed"] and result["version"] == "0.64.0"
    assert settings.read_bytes() == original and settings.stat().st_mode & 0o777 == 0o640


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
