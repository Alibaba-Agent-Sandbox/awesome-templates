"""Actual IDE, auth, state preservation, ownership and deadline checks."""
import importlib.util
import json
from pathlib import Path
import socket
import sys
import time
import pytest

spec=importlib.util.spec_from_file_location('ide_commands',Path(__file__).with_name('commands.py'))
commands=importlib.util.module_from_spec(spec)
spec.loader.exec_module(commands)


@pytest.fixture(autouse=True)
def workspace(monkeypatch,tmp_path):
    monkeypatch.setenv('WORKSPACE',str(tmp_path))
    yield
    commands.code_server_stop()


def test_actual_pin_and_authenticated_workbench():
    assert commands.code_server_version()=='4.141.0'
    assert commands.code_server_self_test()=='CODE_SERVER_OK'
    assert commands.code_server_status()=={'running':False}


def test_actual_private_config_and_environment_preserve_caller(monkeypatch,tmp_path):
    caller=tmp_path/'caller-config';caller.mkdir();settings=caller/'config.yaml';settings.write_text('caller-owned: preserve\n');settings.chmod(0o640)
    monkeypatch.setenv('XDG_CONFIG_HOME',str(caller));monkeypatch.setenv('ALICLOUD_ACCESS_KEY_SECRET','synthetic-cloud-secret')
    assert commands.code_server_version()=='4.141.0'
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    password='synthetic-private-ide-password'
    result=commands.code_server_start(password,port=port)
    private=Path(commands._STATE['private'].name)
    assert private.stat().st_mode&0o777==0o700
    assert (private/'config.yaml').stat().st_mode&0o777==0o600
    assert password not in json.dumps(result)
    assert b'synthetic-cloud-secret' not in Path('/proc/'+str(commands._STATE['process'].pid)+'/environ').read_bytes()
    assert commands.code_server_status()['running'] is True
    commands.code_server_stop()
    assert not private.exists()
    assert settings.read_text()=='caller-owned: preserve\n' and settings.stat().st_mode&0o777==0o640
    assert not commands._listener_exists(port)
    with socket.socket() as sock:
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        sock.bind(('0.0.0.0',port))


@pytest.mark.parametrize('kwargs',[{'password':'short'},{'password':'x'*257},{'port':9000},{'port':80},{'timeout_s':0},{'timeout_s':121}])
def test_invalid_arguments_start_nothing(monkeypatch,kwargs):
    monkeypatch.setattr(commands,'_executable',lambda:pytest.fail('invalid arguments must not execute'))
    with pytest.raises(ValueError):commands.code_server_start(**({'password':'valid-synthetic-password'}|kwargs))
    assert commands.code_server_status()=={'running':False}


def test_unrelated_listener_is_preserved():
    with socket.socket() as sock:
        sock.bind(('0.0.0.0',0));sock.listen();port=sock.getsockname()[1]
        assert commands._listener_exists(port)
        with pytest.raises(RuntimeError,match='already in use'):
            commands.code_server_start('synthetic-test-password',port=port)
        assert sock.getsockname()[1]==port
    assert commands.code_server_status()=={'running':False}


def test_real_readiness_deadline_cleans_redirected_child(monkeypatch,tmp_path):
    marker=tmp_path/'leak'
    child='import pathlib,time;time.sleep(2);pathlib.Path('+repr(str(marker))+').write_text("leaked")'
    executable=tmp_path/'fake-ide'
    executable.write_text('#!'+sys.executable+'\nimport subprocess,sys,time\nsubprocess.Popen([sys.executable,"-c",'+repr(child)+'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\ntime.sleep(10)\n')
    executable.chmod(0o755)
    monkeypatch.setattr(commands,'_executable',lambda:str(executable))
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    with pytest.raises(RuntimeError,match='readiness deadline'):
        commands.code_server_start('synthetic-test-password',port=port,timeout_s=1)
    time.sleep(1.2)
    assert not marker.exists() and commands.code_server_status()=={'running':False}


def test_cleanup_failure_retains_ownership(monkeypatch):
    class Process:pid=424242
    process=Process();commands._STATE.update(process=process,owner='synthetic-no-matching-owner',pidfds={})
    def denied(*_):raise PermissionError('synthetic denial')
    with monkeypatch.context() as patch:
        patch.setattr(commands.os,'killpg',denied)
        with pytest.raises(PermissionError):commands.code_server_stop()
        assert commands._STATE['process'] is process
    commands._STATE.clear()
