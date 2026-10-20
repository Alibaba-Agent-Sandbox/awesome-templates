"""Authored local guard/process controls; no native browser or model claim."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import threading
import pytest

s=importlib.util.spec_from_file_location('stagehand_commands_fixture',Path(__file__).with_name('commands.py'))
c=importlib.util.module_from_spec(s)
s.loader.exec_module(c)


@pytest.mark.parametrize('params',[
    {'task':'','url':'https://example.invalid'}, {'task':'x','url':'file:///etc/passwd'},
    {'task':'x','url':'https://user:pass@example.invalid'}, {'task':'x','url':'https://example.invalid','command_timeout':True},
    {'task':'x','url':'https://example.invalid','command_timeout':601}, {'task':'x'*32769,'url':'https://example.invalid'},
    {'task':'x','url':'https://example.invalid','extract_instruction':False}, {'task':'x','url':'https://example.invalid:invalid'},
])
def test_invalid_arguments_fail_before_native_or_model(params,monkeypatch):
    monkeypatch.setattr(c,'_invoke',lambda *_:pytest.fail('native invocation forbidden'))
    with pytest.raises(ValueError):c.stagehand(**params)


def test_missing_configuration_and_symlink_preserve_caller_files(tmp_path,monkeypatch):
    monkeypatch.setattr(c,'_ROOT',tmp_path);monkeypatch.setattr(c,'_CONFIG',{'API_KEY':'','BASE_URL':'','MODEL':''})
    with pytest.raises(RuntimeError,match='required'):c.stagehand('x','https://example.invalid')
    monkeypatch.setattr(c,'_CONFIG',{'API_KEY':'fixture','BASE_URL':'https://model.example.invalid/v1','MODEL':'fixture'})
    outside=tmp_path/'caller';outside.mkdir();sentinel=outside/'sentinel';sentinel.write_text('untouched')
    (tmp_path/'stagehand-artifacts').symlink_to(outside,target_is_directory=True)
    with pytest.raises(ValueError,match='symlink'):c.stagehand('x','https://example.invalid')
    assert list(outside.iterdir())==[sentinel] and sentinel.read_text()=='untouched'


def test_busy_operation_cannot_overwrite_active_lifecycle():
    c._LOCK.acquire()
    try:
        with pytest.raises(RuntimeError,match='active'):c.stagehand_version()
    finally:c._LOCK.release()


def test_real_authored_timeout_and_output_limit_stop_owned_process(tmp_path):
    process=c._PROCESS
    for source,timeout,error in [('import time;time.sleep(30)',1,'timeout'),("import sys;sys.stdout.write('x'*300000);sys.stdout.flush()",10,'output')]:
        with pytest.raises(RuntimeError,match=error):process.run([sys.executable,'-c',source],cwd=tmp_path,env={'PATH':os.environ['PATH']},timeout=timeout)


def test_real_authored_memfd_stdin_does_not_forward_host_secret(tmp_path):
    key='synthetic-only-private-value';fd=os.memfd_create('stagehand-authored-fixture',os.MFD_CLOEXEC)
    with os.fdopen(fd,'w+b') as source:
        source.write(json.dumps({'key':key}).encode());source.seek(0)
        code,out,_=c._PROCESS.run([sys.executable,'-c',"import os,sys,json;v=json.load(sys.stdin);assert 'HOST_PRIVATE_KEY' not in os.environ;print(len(v['key']))"],cwd=tmp_path,env={'PATH':os.environ['PATH']},timeout=10,input_file=source)
    assert code==0 and int(out)==len(key) and key not in out
