"""Real local guards/process fixtures; no native Muse/model execution."""
import importlib.util,os,sys
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('muse_command_controls',Path(__file__).with_name('commands.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

@pytest.mark.parametrize('args',[{'prompt':''},{'prompt':'x\0y'},{'prompt':'x'*32769},{'prompt':'x','command_timeout':True},{'prompt':'x','command_timeout':0},{'prompt':'x','command_timeout':601},{'prompt':'x','cwd':'/outside-workspace'}])
def test_invalid_input_refused_before_any_native_or_model_call(tmp_path,monkeypatch,args):
    monkeypatch.setattr(module,'ROOT',tmp_path)
    monkeypatch.setattr(module,'binary',lambda:pytest.fail('native was invoked for invalid input'))
    with pytest.raises(ValueError):module.muse(**args)


def test_workspace_symlink_escape_refused(tmp_path,monkeypatch):
    root=tmp_path/'root';root.mkdir();outside=tmp_path/'outside';outside.mkdir();(root/'escape').symlink_to(outside,target_is_directory=True);monkeypatch.setattr(module,'ROOT',root)
    with pytest.raises(ValueError):module.workspace('escape')


def test_minimal_native_environment_and_recursive_redaction(tmp_path,monkeypatch):
    monkeypatch.setenv('OPERATOR_SECRET','SYNTHETIC_OPERATOR_SECRET');monkeypatch.setattr(module,'MODEL',{'MODEL_API_KEY':'SYNTHETIC_MODEL_SECRET','MODEL_BASE_URL':'https://approved.invalid/v1','MODEL':'unit-model'});env=module.environment(tmp_path)
    assert env['HOME']==str(tmp_path)and not any('KEY'in k or'SECRET'in k or'TOKEN'in k for k in env)
    assert module.redact({'nested':['SYNTHETIC_MODEL_SECRET https://approved.invalid/v1']})=={'nested':['[REDACTED] [REDACTED]']}


def test_anonymous_stdin_fixed_owned_process_and_output(tmp_path):
    fd=os.memfd_create('muse-synthetic-input',os.MFD_CLOEXEC)
    with os.fdopen(fd,'w+b')as stream:
        stream.write(b'FIXED_NON_EXECUTABLE_INPUT');stream.seek(0)
        code,out,err=module.PROCESS.run([sys.executable,'-I','-c','import sys;print(sys.stdin.read())'],cwd=tmp_path,env={'PATH':'/usr/bin:/bin','HOME':str(tmp_path)},timeout=5,input_file=stream)
    assert code==0 and out=='FIXED_NON_EXECUTABLE_INPUT\n'and err==''


def test_owned_process_timeout_and_output_budget(tmp_path):
    with pytest.raises(RuntimeError,match='timeout'):
        module.PROCESS.run([sys.executable,'-I','-c','import time;time.sleep(10)'],cwd=tmp_path,env={'PATH':'/usr/bin:/bin'},timeout=.15)
    with pytest.raises(RuntimeError,match='exceeded256KiB'):
        module.PROCESS.run([sys.executable,'-I','-c','print("x"*300000)'],cwd=tmp_path,env={'PATH':'/usr/bin:/bin'},timeout=3)
