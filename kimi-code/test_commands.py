"""Real process lifecycle, argument and credential boundaries for Kimi turns."""
import importlib.util
import json
from pathlib import Path
import sys
import time

import pytest

spec = importlib.util.spec_from_file_location("kimi_commands", Path(__file__).with_name("commands.py"))
commands = importlib.util.module_from_spec(spec)
spec.loader.exec_module(commands)


def configured(monkeypatch, tmp_path):
    for key, value in {"WORKSPACE": str(tmp_path), "KIMI_MODEL_NAME": "example-model",
                       "KIMI_MODEL_API_KEY": "synthetic-model-secret",
                       "KIMI_MODEL_BASE_URL": "https://example.invalid/v1"}.items():
        monkeypatch.setenv(key, value)


def test_explicit_permission_literal_argv_and_private_state_cleanup(monkeypatch, tmp_path):
    configured(monkeypatch, tmp_path)
    monkeypatch.setenv("ALICLOUD_ACCESS_KEY_SECRET", "synthetic-cloud-secret")
    monkeypatch.setattr(commands, "_executable", lambda: "kimi")
    calls = []
    def run(argv, **kwargs):
        assert Path(kwargs["env"]["KIMI_CODE_HOME"]).is_dir()
        assert "ALICLOUD_ACCESS_KEY_SECRET" not in kwargs["env"]
        assert kwargs["env"]["KIMI_MODEL_API_KEY"] == "synthetic-model-secret"
        calls.append((argv, kwargs))
        return "{}"
    monkeypatch.setattr(commands, "_run", run)
    prompt = 'fix $(touch NEVER); "quoted"'
    with pytest.raises(RuntimeError, match="explicit allow_tools=True"):
        commands.kimi(prompt)
    assert calls == []
    assert commands.kimi(prompt, allow_tools=True) == "{}"
    assert calls[0][0] == ["kimi", "--prompt", prompt, "--output-format", "stream-json"]
    assert "--auto" not in calls[0][0]
    assert not Path(calls[0][1]["env"]["KIMI_CODE_HOME"]).exists()



def test_missing_model_never_starts_login(monkeypatch, tmp_path):
    configured(monkeypatch, tmp_path)
    monkeypatch.delenv("KIMI_MODEL_API_KEY")
    monkeypatch.setattr(commands, "_run", lambda *a, **k: pytest.fail("no interactive fallback"))
    with pytest.raises(RuntimeError, match="required"):
        commands.kimi("task")


@pytest.mark.parametrize("kwargs", [{"prompt": " "}, {"prompt": "x" * 65537}, {"command_timeout": 0}, {"command_timeout": 1801}])
def test_invalid_arguments_fail_before_process(monkeypatch, kwargs):
    monkeypatch.setattr(commands, "_run", lambda *a, **k: pytest.fail("invalid invocation"))
    with pytest.raises(ValueError):
        commands.kimi(**({"prompt": "task"} | kwargs))


@pytest.mark.parametrize("exit_code", [0, 7])
def test_completed_leader_cleans_redirected_descendant(tmp_path, exit_code):
    marker = tmp_path / "late"
    child = "import time,pathlib;time.sleep(.3);pathlib.Path(" + repr(str(marker)) + ").write_text('leaked')"
    code = ("import subprocess,sys;subprocess.Popen([sys.executable,'-c'," + repr(child) +
            "],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);sys.exit(" + str(exit_code) + ")")
    result, _, _ = commands._run_process([sys.executable, "-c", code], cwd=str(tmp_path), timeout=3)
    assert result == exit_code
    time.sleep(.4)
    assert not marker.exists()


def test_timeout_and_output_limit_fail_closed(tmp_path):
    with pytest.raises(RuntimeError, match="timed out"):
        commands._run_process([sys.executable, "-c", "import time;time.sleep(10)"], cwd=str(tmp_path), timeout=.05)
    with pytest.raises(RuntimeError, match="8 MiB"):
        commands._run_process([sys.executable, "-c", "import sys;sys.stdout.write('a'*10000000)"], cwd=str(tmp_path), timeout=5)


def test_real_process_output_redacts_json_secret(monkeypatch, tmp_path):
    configured(monkeypatch, tmp_path)
    monkeypatch.setenv("KIMI_MODEL_API_KEY", 'synthetic-"quoted"-secret')
    output = commands._run([sys.executable, "-c", "import os,json;print(json.dumps(os.environ['KIMI_MODEL_API_KEY']))"],
                           timeout=5)
    assert "synthetic" not in output and "REDACTED" in output
