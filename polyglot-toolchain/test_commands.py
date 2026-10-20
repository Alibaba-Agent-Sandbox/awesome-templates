"""Real process and owned artifact behavior; installed pins are checked in L1/L2."""
import importlib.util
from pathlib import Path
import sys
import time

import pytest

spec = importlib.util.spec_from_file_location('polyglot_commands', Path(__file__).with_name('commands.py'))
commands = importlib.util.module_from_spec(spec)
spec.loader.exec_module(commands)


def test_actual_subprocess_output():
    assert commands._run([sys.executable, '-c', 'print(6*7)']) == '42'


@pytest.mark.parametrize('status', [0, 7])
def test_owned_redirected_descendant_is_stopped(tmp_path, status):
    marker = tmp_path/'leak'
    child = 'import time,pathlib;time.sleep(.3);pathlib.Path('+repr(str(marker))+').write_text("leaked")'
    leader = 'import subprocess,sys;subprocess.Popen([sys.executable,"-c",'+repr(child)+'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,stdin=subprocess.DEVNULL);sys.exit('+str(status)+')'
    if status:
        with pytest.raises(RuntimeError,match='toolchain command failed'):
            commands._run([sys.executable,'-c',leader])
    else:
        assert commands._run([sys.executable,'-c',leader]) == ''
    time.sleep(.4)
    assert not marker.exists()


def test_real_deadline_stops_owned_process(monkeypatch, tmp_path):
    marker=tmp_path/'leak'
    code='import time,pathlib;time.sleep(.3);pathlib.Path('+repr(str(marker))+').write_text("leaked")'
    clock=iter([0.,100.])
    monkeypatch.setattr(commands.time,'monotonic',lambda:next(clock,100.))
    with pytest.raises(TimeoutError,match='exceeded'):
        commands._run([sys.executable,'-c',code])
    time.sleep(.4)
    assert not marker.exists()


def test_native_children_exclude_credentials_and_injected_tool_options(monkeypatch):
    import json
    for name in ['OPENAI_API_KEY','ALICLOUD_ACCESS_KEY_SECRET','ABX_SERVER_TOKEN','JAVA_TOOL_OPTIONS','LD_PRELOAD']:
        monkeypatch.setenv(name,'synthetic-do-not-inherit')
    monkeypatch.setenv('GOTOOLCHAIN','auto')
    output=commands._run([sys.executable,'-c','import json,os;names=["OPENAI_API_KEY","ALICLOUD_ACCESS_KEY_SECRET","ABX_SERVER_TOKEN","JAVA_TOOL_OPTIONS","LD_PRELOAD","GOTOOLCHAIN"];print(json.dumps({name:os.environ[name] for name in names if name in os.environ}))'])
    env=json.loads(output.splitlines()[0])
    assert not any(name in env for name in ['OPENAI_API_KEY','ALICLOUD_ACCESS_KEY_SECRET','ABX_SERVER_TOKEN','JAVA_TOOL_OPTIONS','LD_PRELOAD'])
    assert env['GOTOOLCHAIN']=='local'


def test_actual_output_limit_stops_noisy_native_process():
    code='import os;data=b"x"*65536\nwhile True:os.write(1,data)'
    with pytest.raises(RuntimeError,match='output exceeded'):
        commands._run([sys.executable,'-c',code])
