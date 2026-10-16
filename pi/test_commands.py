"""Pi runtime regressions; fake executable fixtures never count as model acceptance."""
import importlib.util
import json
from pathlib import Path
import sys
import time
import traceback

import pytest

SPEC = importlib.util.spec_from_file_location("pi_template_commands", Path(__file__).with_name("commands.py"))
commands = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(commands)


def configure(monkeypatch, tmp_path):
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    monkeypatch.setenv("PI_BASE_URL", "https://example.invalid/v1")
    monkeypatch.setenv("PI_MODEL", "synthetic-model")
    monkeypatch.setenv("PI_API_KEY", 'synthetic-雪-"quoted"-key')


def test_setup_is_read_only_without_secret_or_endpoint_disclosure(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    monkeypatch.setattr(commands.shutil, "which", lambda name: None)
    assert commands.pi_setup_check() == {"installed":False,"version":"","pinned_version":"1.3.0",
        "api_key_set":True,"base_url_set":True,"model_set":True,"workspace":str(tmp_path)}
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("missing", ["PI_BASE_URL", "PI_MODEL", "PI_API_KEY"])
def test_missing_configuration_never_launches_or_logs_in(monkeypatch, tmp_path, missing):
    configure(monkeypatch, tmp_path)
    monkeypatch.delenv(missing)
    monkeypatch.setattr(commands, "_run", lambda *a, **k: pytest.fail("must not launch"))
    with pytest.raises(RuntimeError, match="required"):
        commands.pi("test")


@pytest.mark.parametrize("allow_tools", [False, True])
def test_explicit_tools_and_ephemeral_configuration(monkeypatch, tmp_path, allow_tools):
    configure(monkeypatch, tmp_path)
    monkeypatch.setattr(commands, "_executable", lambda: "pi")
    captured = {}
    prompt = '- @private $(touch NEVER); "quoted"'
    def run(argv, **kwargs):
        captured.update(argv=argv, **kwargs)
        config = Path(kwargs["env"]["PI_CODING_AGENT_DIR"])
        captured["config"] = config
        model = json.loads((config / "models.json").read_text())
        assert model["providers"]["abx"]["apiKey"] == "$PI_API_KEY"
        assert commands.os.environ["PI_API_KEY"] not in (config / "models.json").read_text()
        assert list(config.iterdir()) == [config / "models.json"]
        return "result"
    monkeypatch.setattr(commands, "_run", run)
    assert commands.pi(prompt, allow_tools=allow_tools) == "result"
    argv = captured["argv"]
    assert prompt not in argv and captured["input_text"] == prompt
    assert argv[argv.index("--tools")+1] == ("read,grep,find,ls,edit,write,bash" if allow_tools else "read,grep,find,ls")
    assert {"--no-session", "--offline", "--no-approve", "--no-extensions", "--no-mcp", "--no-skills", "--no-context-files"} <= set(argv)
    assert not captured["config"].exists()


@pytest.mark.parametrize("kwargs", [{"prompt":" "}, {"allow_tools":"false"}, {"command_timeout":0}, {"command_timeout":1801}, {"command_timeout":True}])
def test_invalid_arguments_do_not_launch(monkeypatch, kwargs):
    monkeypatch.setattr(commands, "_run", lambda *a, **k: pytest.fail("must not launch"))
    with pytest.raises(ValueError): commands.pi(**({"prompt":"test"}|kwargs))


@pytest.mark.parametrize("endpoint", ["file:///private", "https://user:secret@example.invalid/v1", "https://example.invalid/v1?key=private", "https://example.invalid/#private"])
def test_embedded_endpoint_credentials_are_rejected(monkeypatch, tmp_path, endpoint):
    configure(monkeypatch, tmp_path)
    monkeypatch.setenv("PI_BASE_URL", endpoint)
    with pytest.raises(ValueError, match="without embedded credentials"):
        commands.pi("test")


@pytest.mark.parametrize("failed", [True, False])
def test_real_process_redacts_raw_and_json_credentials(monkeypatch, tmp_path, failed):
    configure(monkeypatch, tmp_path)
    code = "import os,json,sys;print(os.environ['PI_API_KEY']);print(json.dumps(os.environ['PI_API_KEY']));sys.exit("+str(int(failed))+")"
    if failed:
        with pytest.raises(RuntimeError) as exc: commands._run([sys.executable,"-c",code],timeout=5)
        result = str(exc.value)
    else: result = commands._run([sys.executable,"-c",code],timeout=5)
    secret = commands.os.environ["PI_API_KEY"]
    assert secret not in result and json.dumps(secret)[1:-1] not in result
    assert "[REDACTED]" in result


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
    import subprocess
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


def test_cancellation_cleans_group_and_ephemeral_profile(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    child_marker = tmp_path / "cancel-survivor"
    started = tmp_path / "started"
    child = f"import time;time.sleep(1.5);open({str(child_marker)!r},'w').write('bad')"
    leader = ("import subprocess,sys,time,pathlib;subprocess.Popen([sys.executable,'-c',"+repr(child)+
        "],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);"
        f"pathlib.Path({str(started)!r}).write_text('ready');time.sleep(30)")
    original = commands.os.waitid
    def cancel(*args):
        if started.exists(): raise KeyboardInterrupt("synthetic cancellation")
        return original(*args)
    monkeypatch.setattr(commands.os,"waitid",cancel)
    with pytest.raises(KeyboardInterrupt):
        commands._run_process([sys.executable,"-c",leader],cwd=str(tmp_path),timeout=5)
    time.sleep(1.7)
    assert not child_marker.exists()


def test_ephemeral_profile_is_removed_on_cli_error(monkeypatch, tmp_path):
    configure(monkeypatch,tmp_path)
    monkeypatch.setattr(commands,"_executable",lambda:"pi")
    profiles=[]
    def fail(*args,**kwargs):
        profiles.append(Path(kwargs["env"]["PI_CODING_AGENT_DIR"]))
        raise RuntimeError("synthetic CLI failure")
    monkeypatch.setattr(commands,"_run",fail)
    with pytest.raises(RuntimeError,match="synthetic CLI failure"):commands.pi("test")
    assert profiles and not profiles[0].exists()
