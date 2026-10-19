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
