"""Qoder command regressions: credentials, argv, cwd, errors and cancellation."""
import importlib.util
import json
from pathlib import Path
import sys
import time
import traceback

import pytest

SPEC = importlib.util.spec_from_file_location("qoder_template_commands", Path(__file__).with_name("commands.py"))
commands = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(commands)


def test_setup_is_read_only_and_does_not_expose_pat(monkeypatch, tmp_path):
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    monkeypatch.setenv("QODER_PERSONAL_ACCESS_TOKEN", "synthetic-personal-token")
    monkeypatch.setattr(commands.shutil, "which", lambda name: None)
    original = tmp_path / "settings.json"
    original.write_text('{"private":"synthetic-config-value"}')
    before = original.read_bytes()
    state = commands.qoder_setup_check()
    assert state["pat_set"] is True and state["installed"] is False
    assert "synthetic-personal-token" not in json.dumps(state)
    assert original.read_bytes() == before and list(tmp_path.iterdir()) == [original]


def test_missing_pat_never_launches_cli(monkeypatch):
    monkeypatch.delenv("QODER_PERSONAL_ACCESS_TOKEN", raising=False)
    monkeypatch.setattr(commands, "_run", lambda *a, **k: pytest.fail("interactive login must not run"))
    with pytest.raises(RuntimeError, match="QODER_PERSONAL_ACCESS_TOKEN is required"):
        commands.qoder("repair code")


def test_pinned_flags_and_argv_quoting(monkeypatch, tmp_path):
    monkeypatch.setenv("QODER_PERSONAL_ACCESS_TOKEN", "synthetic-personal-token")
    monkeypatch.setattr(commands, "_executable", lambda: "qodercli")
    captured = {}
    def run(argv, **kwargs):
        captured.update(argv=argv, **kwargs)
        return "{}"
    monkeypatch.setattr(commands, "_run", run)
    prompt = 'fix code; $(touch NEVER) "quoted"'
    assert commands.qoder(prompt, cwd=str(tmp_path), command_timeout=18) == "{}"
    assert captured["argv"][:3] == ["qodercli", "--print", prompt]
    assert captured["argv"][captured["argv"].index("--permission-mode") + 1] == "accept_edits"
    assert "--no-session-persistence" in captured["argv"]
    assert "--max-turns" not in captured["argv"]
    assert captured["timeout"] == 18 and captured["cwd"] == str(tmp_path)
    assert captured["env"]["CI"] == "1"


@pytest.mark.parametrize("kwargs", [{"prompt": " "}, {"command_timeout": 0}, {"command_timeout": 1801}])
def test_invalid_input_fails_before_process(monkeypatch, kwargs):
    monkeypatch.setattr(commands, "_run", lambda *a, **k: pytest.fail("invalid input must not run"))
    with pytest.raises(ValueError):
        commands.qoder(**({"prompt": "test"} | kwargs))


@pytest.mark.parametrize("failed", [True, False])
def test_secrets_redacted_on_success_and_error(monkeypatch, tmp_path, failed):
    secret = 'synthetic-"quoted"-token'
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    monkeypatch.setenv("QODER_PERSONAL_ACCESS_TOKEN", secret)
    code = "import os,json,sys;print(json.dumps(os.environ['QODER_PERSONAL_ACCESS_TOKEN']));sys.exit(" + str(int(failed)) + ")"
    if failed:
        with pytest.raises(RuntimeError) as exc:
            commands._run([sys.executable, "-c", code], timeout=5)
        output = str(exc.value)
    else:
        output = commands._run([sys.executable, "-c", code], timeout=5)
    assert secret not in output and json.dumps(secret)[1:-1] not in output
    assert "[REDACTED]" in output


def test_compatibility_script_uses_workspace_and_propagates_failure(monkeypatch, tmp_path):
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    script = tmp_path / "main.py"
    script.write_text("from pathlib import Path\nprint(Path.cwd().name)\n")
    assert commands.qoder_run().strip() == tmp_path.name
    script.write_text("raise RuntimeError('expected compatibility failure')")
    with pytest.raises(RuntimeError, match="expected compatibility failure"):
        commands.qoder_run()
    with pytest.raises(ValueError, match="existing directory"):
        commands._workdir("missing-directory")


def test_timeout_kills_owned_descendants_and_omits_private_argv(monkeypatch, tmp_path):
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    marker = tmp_path / "survived"
    child = f"import time;time.sleep(2);open({str(marker)!r},'w').write('bad')"
    parent = "import subprocess,sys,time;subprocess.Popen([sys.executable,'-c'," + repr(child) + "]);time.sleep(30)"
    private_prompt = "private-" + "prompt"
    with pytest.raises(RuntimeError, match="timed out") as exc:
        commands._run([sys.executable, "-c", parent, private_prompt], timeout=1)
    assert "private-prompt" not in "".join(traceback.format_exception(exc.value))
    time.sleep(1.2)
    assert not marker.exists()


@pytest.mark.parametrize("exit_code", [0, 7])
def test_leader_exit_cleans_owned_descendants(monkeypatch, tmp_path, exit_code):
    import time
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    marker = tmp_path / "escaped-cleanup"
    child = f"import time;time.sleep(1.5);open({str(marker)!r},'w').write('bad')"
    leader = ("import subprocess,sys;subprocess.Popen([sys.executable,'-c'," + repr(child) +
              "],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);"
              "print('leader-output',flush=True);sys.exit(" + str(exit_code) + ")")
    code, stdout, stderr = commands._run_process([sys.executable, "-c", leader], cwd=str(tmp_path), timeout=5)
    assert code == exit_code and stdout == "leader-output\n" and stderr == ""
    time.sleep(1.7)
    assert not marker.exists()


def test_runner_drains_large_stdout_and_stderr_without_deadlock(tmp_path):
    code, stdout, stderr = commands._run_process([sys.executable, "-c",
        "import sys;sys.stdout.write('x'*200000);sys.stderr.write('y'*200000)"], cwd=str(tmp_path), timeout=5)
    assert code == 0 and stdout == "x"*200000 and stderr == "y"*200000


def test_redaction_handles_unicode_json_and_raw(monkeypatch):
    secret = 'synthetic-雪-"quoted"-token'
    monkeypatch.setenv("SYNTHETIC_API_KEY", secret)
    variants = [secret, json.dumps(secret)[1:-1], json.dumps(secret, ensure_ascii=False)[1:-1]]
    for variant in variants:
        assert commands._redact(variant) == "[REDACTED]"


def test_deadline_kills_term_ignoring_descendant_after_leader_exits(monkeypatch, tmp_path):
    import time
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    marker = tmp_path / "term-ignoring-survivor"
    child = ("import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);"
             f"time.sleep(2);open({str(marker)!r},'w').write('bad')")
    leader = ("import subprocess,sys,time;subprocess.Popen([sys.executable,'-c'," + repr(child) +
              "],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(30)")
    with pytest.raises(RuntimeError, match="timed out"):
        commands._run_process([sys.executable,"-c",leader], cwd=str(tmp_path), timeout=1)
    time.sleep(1.3)
    assert not marker.exists()
