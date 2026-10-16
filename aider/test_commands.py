"""Offline guards/owned-process regressions. Fake CLI tests are not model acceptance."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

import pytest

SPEC = importlib.util.spec_from_file_location("aider_template_commands", Path(__file__).with_name("commands.py"))
commands = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(commands)


def configure(monkeypatch, tmp_path):
    monkeypatch.setenv("WORKSPACE", str(tmp_path))
    monkeypatch.setenv("AIDER_API_KEY", 'synthetic-雪-"quoted"-key')
    monkeypatch.setenv("AIDER_BASE_URL", "https://example.invalid/v1")
    monkeypatch.setenv("AIDER_MODEL", "synthetic-model")
    monkeypatch.setattr(commands, "_home_guard", lambda: None)
    monkeypatch.setattr(commands, "_executable", lambda: "aider")
    monkeypatch.setattr(commands, "_run_process", lambda *a, **k: (0, "true\n", ""))


@pytest.mark.parametrize("name", [".aider.conf.yml", ".env", ".aider.model.settings.yml", ".aider.model.metadata.json", ".aider/oauth-keys.env"])
def test_native_home_configuration_refuses_before_cli(monkeypatch, tmp_path, name):
    target = tmp_path / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("synthetic malicious configuration")
    monkeypatch.setattr(commands.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(commands, "_executable", lambda: pytest.fail("must not launch"))
    with pytest.raises(RuntimeError, match="fresh dedicated sandbox"):
        commands.aider_version()
    assert target.read_text() == "synthetic malicious configuration"


@pytest.mark.parametrize("missing", ["AIDER_API_KEY", "AIDER_BASE_URL", "AIDER_MODEL"])
def test_missing_model_settings_do_not_launch(monkeypatch, tmp_path, missing):
    configure(monkeypatch, tmp_path)
    monkeypatch.delenv(missing)
    monkeypatch.setattr(commands, "_executable", lambda: pytest.fail("must not launch"))
    with pytest.raises(RuntimeError, match="required"):
        commands.aider("test")


@pytest.mark.parametrize("kwargs", [{"prompt":" "}, {"allow_write":"false"}, {"command_timeout":True}, {"command_timeout":0}, {"command_timeout":1801}, {"allow_write":True}])
def test_invalid_typed_arguments_fail_before_cli(monkeypatch, tmp_path, kwargs):
    configure(monkeypatch, tmp_path)
    with pytest.raises(ValueError): commands.aider(**({"prompt":"test"}|kwargs))


@pytest.mark.parametrize("names", [["../outside"], ["/absolute"], [".env"], [".git/config"], [".aider.conf.yml"], ["file.py", "file.py"], "not-a-list", [4]])
def test_selected_file_boundaries(tmp_path, names):
    with pytest.raises(ValueError): commands._file_paths(tmp_path, json.dumps(names))


def test_symlink_source_parent_is_rejected(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "project"
    root.mkdir()
    (root / "linked").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symbolic links"):
        commands._file_paths(root, '["linked/source.py"]')


@pytest.mark.parametrize("writable", [False, True])
def test_real_cli_argv_staging_and_explicit_writeback(monkeypatch, tmp_path, writable):
    configure(monkeypatch, tmp_path)
    original = tmp_path / "calculator.py"
    original.write_text("broken")
    original.chmod(0o755)
    (tmp_path / ".env").write_text("MUST_NOT_BE_COPIED=synthetic")
    (tmp_path / ".aider.conf.yml").write_text("malicious project config")
    profiles = []
    prompt = 'private prompt $(touch NEVER); "quoted"'
    def checked(argv, *, cwd, timeout, env):
        profile = cwd.parent
        profiles.append(profile)
        assert sorted(p.name for p in cwd.iterdir()) == ["REPORT.md", "calculator.py"]
        assert prompt not in argv and (profile / "message.txt").read_text() == prompt
        assert argv[argv.index("--chat-mode")+1] == ("whole" if writable else "ask")
        assert env.get("HOME") == commands.os.environ.get("HOME") and "AIDER_API_KEY" not in env
        assert env["OPENAI_API_KEY"] == commands.os.environ["AIDER_API_KEY"]
        assert env["PYTHON_DOTENV_DISABLED"] == "1"
        assert {"--no-auto-commits", "--no-dirty-commits", "--no-suggest-shell-commands", "--disable-playwright"} <= set(argv)
        for file in profile.iterdir():
            if file.is_file(): assert env["OPENAI_API_KEY"] not in file.read_text()
        (cwd / "calculator.py").write_text("fixed")
        (cwd / "REPORT.md").write_text("new artifact")
        return "answer", ""
    monkeypatch.setattr(commands, "_checked", checked)
    result = commands.aider(prompt, files='["calculator.py","REPORT.md"]', allow_write=writable)
    assert result["stdout"] == "answer" and result["exit_code"] == 0
    assert original.read_text() == ("fixed" if writable else "broken")
    assert (tmp_path / "REPORT.md").exists() is writable
    assert result["changed_files"] == (["calculator.py", "REPORT.md"] if writable else [])
    assert original.stat().st_mode & 0o777 == 0o755
    assert all(not p.exists() for p in profiles)
    assert (tmp_path / ".env").read_text() == "MUST_NOT_BE_COPIED=synthetic"


@pytest.mark.parametrize("change", ["stale", "source-link", "stage-link"])
def test_stale_or_symlink_writeback_never_overwrites_original(monkeypatch, tmp_path, change):
    configure(monkeypatch, tmp_path)
    source = tmp_path / "source.py"
    source.write_text("original")
    elsewhere = tmp_path / "outside.txt"
    elsewhere.write_text("untouched")
    def checked(argv, *, cwd, **kwargs):
        (cwd / "source.py").write_text("model result")
        if change == "stale": source.write_text("concurrent edit")
        elif change == "source-link": source.unlink(); source.symlink_to(elsewhere)
        else: (cwd / "source.py").unlink(); (cwd / "source.py").symlink_to(elsewhere)
        return "", ""
    monkeypatch.setattr(commands, "_checked", checked)
    with pytest.raises((RuntimeError, ValueError)):
        commands.aider("test", files='["source.py"]', allow_write=True)
    assert elsewhere.read_text() == "untouched"
    if change == "stale": assert source.read_text() == "concurrent edit"


def test_failure_removes_private_prompt_stage_and_omits_upstream_output(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    profiles = []
    def fail(argv, *, cwd, **kwargs):
        profiles.append(cwd.parent)
        raise RuntimeError("synthetic CLI failure")
    monkeypatch.setattr(commands, "_checked", fail)
    with pytest.raises(RuntimeError): commands.aider("private prompt")
    assert profiles and not profiles[0].exists()


def test_process_result_redaction_and_generic_errors(monkeypatch, tmp_path):
    secret = 'synthetic-雪-"quoted"-key'
    monkeypatch.setenv("AIDER_API_KEY", secret)
    monkeypatch.setattr(commands, "_run_process", lambda *a, **k: (0, secret+json.dumps(secret), ""))
    out, _ = commands._checked(["test"], cwd=tmp_path, timeout=1, env={})
    assert secret not in out and "[REDACTED]" in out
    monkeypatch.setattr(commands, "_run_process", lambda *a, **k: (7, "private prompt", secret))
    with pytest.raises(RuntimeError) as exc: commands._checked(["test"], cwd=tmp_path, timeout=1, env={})
    assert secret not in str(exc.value) and "private prompt" not in str(exc.value)


@pytest.mark.parametrize("exit_code", [0, 7])
def test_leader_exit_reaps_owned_descendants(tmp_path, exit_code):
    marker = tmp_path / "survived"
    child = f"import time;time.sleep(1.3);open({str(marker)!r},'w').write('bad')"
    leader = "import subprocess,sys;subprocess.Popen([sys.executable,'-c',"+repr(child)+"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);sys.exit("+str(exit_code)+")"
    result = commands._run_process([sys.executable,"-c",leader], cwd=str(tmp_path), timeout=5)
    assert result[0] == exit_code
    time.sleep(1.5)
    assert not marker.exists()


def test_timeout_and_cancellation_reap_owned_group(monkeypatch, tmp_path):
    marker = tmp_path / "cancel-survivor"
    started = tmp_path / "started"
    child = f"import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(2);open({str(marker)!r},'w').write('bad')"
    leader = ("import subprocess,sys,time,pathlib;subprocess.Popen([sys.executable,'-c',"+repr(child)+"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);"
              f"pathlib.Path({str(started)!r}).write_text('ready');time.sleep(30)")
    original = commands.os.waitid
    def cancel(*args):
        if started.exists(): raise KeyboardInterrupt("synthetic cancellation")
        return original(*args)
    monkeypatch.setattr(commands.os, "waitid", cancel)
    with pytest.raises(KeyboardInterrupt): commands._run_process([sys.executable,"-c",leader],cwd=str(tmp_path),timeout=5)
    monkeypatch.setattr(commands.os, "waitid", original)
    with pytest.raises(RuntimeError, match="timed out"):
        commands._run_process([sys.executable,"-c",leader],cwd=str(tmp_path),timeout=1)
    time.sleep(1.2)
    assert not marker.exists()


def test_bare_git_repository_is_not_a_working_tree(monkeypatch, tmp_path):
    configure(monkeypatch, tmp_path)
    monkeypatch.setattr(commands, "_run_process", lambda *a, **k: (0,"false\n",""))
    monkeypatch.setattr(commands, "_checked", lambda *a, **k: pytest.fail("must not launch Aider"))
    with pytest.raises(ValueError, match="existing git working tree"):
        commands.aider("test")
