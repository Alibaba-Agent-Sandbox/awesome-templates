"""Actual native parser/bytes and real process ownership controls."""
import importlib.util
from pathlib import Path
import sys
import time
import pytest

spec=importlib.util.spec_from_file_location('patch_commands',Path(__file__).with_name('commands.py'))
commands=importlib.util.module_from_spec(spec)
spec.loader.exec_module(commands)


@pytest.fixture(autouse=True)
def workspace(monkeypatch,tmp_path):
    monkeypatch.setenv('WORKSPACE',str(tmp_path))


def test_actual_version_and_mutation_lifecycle():
    assert commands.apply_patch_version()=='codex-cli 0.162.1'
    assert commands.apply_patch_smoke()=='APPLY_PATCH_OK'


@pytest.mark.parametrize('path',['../escape','/tmp/escape','a/../../escape',r'a\escape'])
def test_relative_scope_rejects_before_any_write(tmp_path,path):
    patch='*** Begin Patch\n*** Add File: allowed\n+must-not-write\n*** Add File: '+path+'\n+escape\n*** End Patch\n'
    with pytest.raises(ValueError):commands.apply_patch(patch)
    assert not (tmp_path/'allowed').exists()


def test_symlink_scope_rejected(tmp_path):
    (tmp_path/'linked').symlink_to('/tmp',target_is_directory=True)
    with pytest.raises(ValueError,match='escapes|symlink'):
        commands.apply_patch('*** Begin Patch\n*** Add File: linked/escape\n+no\n*** End Patch\n')


def test_real_parser_failure_and_unicode_literal(tmp_path):
    result=commands.apply_patch('not a patch')
    assert result['exit_code']!=0 and result['stderr']
    text='中文 $(touch NEVER)'
    result=commands.apply_patch('*** Begin Patch\n*** Add File: literal.txt\n+'+text+'\n*** End Patch\n')
    assert result['exit_code']==0 and (tmp_path/'literal.txt').read_text()==text+'\n'
    assert not (tmp_path/'NEVER').exists()


@pytest.mark.parametrize('status',[0,7])
def test_real_owned_redirected_descendant(tmp_path,status):
    marker=tmp_path/'leak'
    child='import time,pathlib;time.sleep(.3);pathlib.Path('+repr(str(marker))+').write_text("leaked")'
    leader='import subprocess,sys;subprocess.Popen([sys.executable,"-c",'+repr(child)+'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,stdin=subprocess.DEVNULL);sys.exit('+str(status)+')'
    code,_,_=commands._run_process([sys.executable,'-c',leader],cwd=str(tmp_path),timeout=2)
    assert code==status
    time.sleep(.4)
    assert not marker.exists()


def test_real_timeout_and_output_bound(tmp_path):
    with pytest.raises(RuntimeError,match='timed out'):
        commands._run_process([sys.executable,'-c','import time;time.sleep(10)'],cwd=str(tmp_path),timeout=.05)
    with pytest.raises(RuntimeError,match='256 KiB'):
        commands._run_process([sys.executable,'-c','import sys;sys.stdout.write("x"*300000)'],cwd=str(tmp_path),timeout=2)
