"""Behavior regressions for Qwen configuration, CLI arguments and cancellation."""
import importlib.util
import json
from pathlib import Path
import sys
import time
import traceback

import pytest

SPEC = importlib.util.spec_from_file_location("qwen_template_commands", Path(__file__).with_name("commands.py"))
commands = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(commands)


def test_setup_never_creates_or_rewrites_settings(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    monkeypatch.setattr(commands.shutil, "which", lambda name: None)
    result = commands.qwen_setup_check()
    assert not result["installed"] and not (tmp_path / ".qwen").exists()
    path = tmp_path / ".qwen" / "settings.json"
    path.parent.mkdir()
    original = '{"private":"synthetic-settings-secret","custom":true}\n'
    path.write_text(original)
    path.chmod(0o640)
    result = commands.qwen_setup_check()
    assert path.read_text() == original and path.stat().st_mode & 0o777 == 0o640
    assert "synthetic-settings-secret" not in json.dumps(result)


def test_missing_key_never_launches_cli(monkeypatch):
    for name in ("OPENAI_API_KEY", "DASHSCOPE_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(commands, "_run", lambda *a, **k: pytest.fail("no login or model invocation"))
    with pytest.raises(RuntimeError, match="required"):
        commands.qwen("test")


@pytest.mark.parametrize("yolo", [True, False])
def test_real_cli_flags_dashscope_fallback_and_typed_limits(monkeypatch, yolo):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("DASHSCOPE_API_KEY", "synthetic-dashscope-key")
    monkeypatch.setattr(commands, "_executable", lambda: "qwen")
    captured = {}
    def run(argv, **kwargs):
        captured.update(argv=argv, **kwargs)
        return "{}"
    monkeypatch.setattr(commands, "_run", run)
    commands.qwen("edit code", max_turns=7, model="compatible-model", yolo=yolo)
    assert "--max-turns" not in captured["argv"]
    assert captured["argv"][captured["argv"].index("--max-session-turns") + 1] == "7"
    assert captured["env"]["OPENAI_API_KEY"] == "synthetic-dashscope-key"
    assert ("--yolo" in captured["argv"]) is yolo
    assert "--auth-type" in captured["argv"] and "openai" in captured["argv"]
    for kwargs in ({"max_turns": 0}, {"command_timeout": 1801}, {"prompt": " "}):
        with pytest.raises(ValueError):
            commands.qwen(**({"prompt": "test"} | kwargs))


@pytest.mark.parametrize("failed", [True, False])
def test_secret_redacted_from_success_and_failure(monkeypatch, tmp_path, failed):
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    secret = 'synthetic-"quoted"-secret'
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    monkeypatch.setenv("ABX_SERVER_TOKEN", "synthetic-server-token")
    code = "import os,json,sys;print(json.dumps(dict(key=os.environ['OPENAI_API_KEY'], token=os.environ['ABX_SERVER_TOKEN'])));sys.exit(" + str(int(failed)) + ")"
    if failed:
        with pytest.raises(RuntimeError) as exc:
            commands._run([sys.executable, "-c", code], timeout=5)
        output = str(exc.value)
    else:
        output = commands._run([sys.executable, "-c", code], timeout=5)
    assert secret not in output and json.dumps(secret)[1:-1] not in output
    assert "synthetic-server-token" not in output and "[REDACTED]" in output


def test_timeout_kills_owned_descendants_and_hides_argv(monkeypatch, tmp_path):
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    marker = tmp_path / "survived"
    child = f"import time;time.sleep(2);open({str(marker)!r},'w').write('bad')"
    parent = "import subprocess,sys,time;subprocess.Popen([sys.executable,'-c'," + repr(child) + "]);time.sleep(30)"
    private_prompt = "private-prompt"
    with pytest.raises(RuntimeError, match="timed out") as exc:
        commands._run([sys.executable, "-c", parent, private_prompt], timeout=1)
    assert private_prompt not in "".join(traceback.format_exception(exc.value))
    time.sleep(1.2)
    assert not marker.exists()


def test_whitespace_primary_key_uses_dashscope_fallback(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "   ")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "synthetic-fallback-key")
    assert commands._api_key() == "synthetic-fallback-key"


@pytest.mark.parametrize("exit_code", [0, 7])
def test_completed_leader_cleans_redirected_descendants(monkeypatch, tmp_path, exit_code):
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    marker = tmp_path / "escaped-cleanup"
    child = f"import time;time.sleep(1);open({str(marker)!r},'w').write('bad')"
    leader = ("import subprocess,sys;subprocess.Popen([sys.executable,'-c'," + repr(child) +
              "],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);"
              "print('leader-output',flush=True);sys.exit(" + str(exit_code) + ")")
    if exit_code:
        with pytest.raises(RuntimeError):
            commands._run([sys.executable, "-c", leader], timeout=5)
    else:
        assert commands._run([sys.executable, "-c", leader], timeout=5) == "leader-output\n"
    time.sleep(1.2)
    assert not marker.exists(), "a completed coding turn must stop its owned descendants"


def test_runner_drains_both_pipes(monkeypatch, tmp_path):
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    assert commands._run([sys.executable, "-c",
        "import sys;sys.stdout.write('x'*200000);sys.stderr.write('y'*200000)"], timeout=5) == "x"*200000


@pytest.mark.parametrize('base,model', [('', ''), ('https://model.example.invalid/v1', 'owned-model')])
def test_blank_launch_settings_preserve_defaults_or_explicit_service(monkeypatch, base, model):
    monkeypatch.setenv('OPENAI_API_KEY', 'synthetic-key')
    monkeypatch.setenv('OPENAI_BASE_URL', base)
    monkeypatch.setenv('OPENAI_MODEL', model)
    monkeypatch.setattr(commands, '_executable', lambda: 'qwen')
    captured = {}
    monkeypatch.setattr(commands, '_run', lambda argv, **kw: captured.update(argv=argv, **kw) or '{}')
    commands.qwen('owned task')
    assert captured['env']['OPENAI_BASE_URL'] == (base or 'https://dashscope.aliyuncs.com/compatible-mode/v1')
    assert captured['env']['OPENAI_MODEL'] == (model or 'qwen3-coder-plus')
    assert captured['argv'][captured['argv'].index('--model') + 1] == (model or 'qwen3-coder-plus')

