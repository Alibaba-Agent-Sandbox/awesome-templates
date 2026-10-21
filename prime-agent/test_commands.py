"""Authored boundaries/protocol fixtures only; never claim original agent execution."""
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import pytest


def load(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file))
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value

c=load('prime_command_boundary_tests','commands.py')
f=load('prime_stream_boundary_tests','filter_native.py')


@pytest.mark.parametrize('parameters',[{'prompt':''},{'prompt':'x\0y'},{'prompt':'x'*32769},{'prompt':'x','cwd':'/outside-workspace'},{'prompt':'x','cwd':'x\0y'},{'prompt':'x','command_timeout':True},{'prompt':'x','command_timeout':0},{'prompt':'x','command_timeout':601}])
def test_invalid_request_cannot_launch_native(monkeypatch,parameters):
    monkeypatch.setattr(c,'run_native',lambda *a,**k:pytest.fail('invalid request reached native CLI'))
    with pytest.raises(ValueError):c.prime_agent(**parameters)


@pytest.mark.parametrize('base',['https://@example.invalid','https://user:pass@example.invalid','https://example.invalid?key=x','https://example.invalid#token','http://public.invalid','https://example.invalid:bad'])
def test_unsafe_provider_route_never_passes_config(monkeypatch,base):
    monkeypatch.setattr(c,'CONFIG',{'MODEL_BASE_URL':base,'MODEL_API_KEY':'synthetic-private-key','MODEL':'fixture-model'})
    with pytest.raises(ValueError):c.validate_config()


def test_private_profile_has_only_environment_key_reference_and_bounded_native_controls(tmp_path,monkeypatch):
    monkeypatch.setattr(c,'CONFIG',{'MODEL_BASE_URL':'http://127.0.0.1:12345/v1','MODEL_API_KEY':'synthetic-private-key','MODEL':'fixture-model'})
    c.profile(tmp_path,True)
    model=json.loads((tmp_path/'agent/models.json').read_text())
    settings=json.loads((tmp_path/'agent/settings.json').read_text())
    assert model['providers']['abx-approved']['apiKey']=='ABX_PRIME_MODEL_KEY'
    assert 'synthetic-private-key'not in (tmp_path/'agent/models.json').read_text()
    assert settings['rlmMaxDepth']==0 and settings['telemetry']['enabled'] is False and settings['factory']['enabled'] is False
    assert (tmp_path/'agent/models.json').stat().st_mode&0o777==0o600
    assert (tmp_path/'agent').stat().st_mode&0o777==0o700


def test_minimal_native_environment_excludes_operator_and_override_values(tmp_path,monkeypatch):
    for name in ['OPENAI_API_KEY','GITHUB_TOKEN','ALICLOUD_ACCESS_KEY_SECRET','PRIME_AGENT_KERNEL_PYTHON','PI_PACKAGE_DIR','PYTHONPATH','PRIME_AGENT_FAUX_SCRIPT']:
        monkeypatch.setenv(name,'unrelated-operator-value')
    env=c.environment(tmp_path,False)
    assert not any(name in env for name in ['OPENAI_API_KEY','GITHUB_TOKEN','ALICLOUD_ACCESS_KEY_SECRET','PI_PACKAGE_DIR','PYTHONPATH','PRIME_AGENT_FAUX_SCRIPT','ABX_PRIME_MODEL_KEY'])
    assert env['PRIME_AGENT_KERNEL_PYTHON']=='/opt/prime-kernel/bin/abx-kernel-python'and env['HOME']==str(tmp_path)


def test_kernel_wrapper_removes_model_key_and_ignores_path_override(tmp_path):
    # Execute only an authored copy with an authored fake interpreter, not the
    # original agent/kernel or any model output on the operator.
    fake=tmp_path/'python';fake.write_text('#!/bin/sh\ntest -z "${ABX_PRIME_MODEL_KEY+x}" || exit 9\nprintf "%s\\n" "$PYTHONPATH"\nprintf "%s\\n" "$1"\n');fake.chmod(0o755)
    wrapper=tmp_path/'kernel';text=Path(__file__).with_name('kernel-python').read_text().replace('/opt/prime-kernel/bin/python',str(fake));wrapper.write_text(text);wrapper.chmod(0o755)
    import subprocess
    value=subprocess.run([str(wrapper),'-c'],env={'PATH':'/usr/bin:/bin','ABX_PRIME_MODEL_KEY':'synthetic-key','PYTHONPATH':'unrelated-override'},capture_output=True,text=True)
    assert value.returncode==0 and value.stdout.splitlines()==['/opt/prime-agent/prime-agent-runtime/src','-c']


def test_filtered_stream_drops_duplicate_updates_and_keeps_original_terminal_bytes():
    records=[{'type':'agent_start'},{'type':'message_update','message':{'text':'partial'}},
             {'type':'turn_end','message':{'role':'assistant'}},
             {'type':'agent_end','messages':[{'role':'assistant','stopReason':'stop'}]}]
    lines=[(json.dumps(value)+'\n').encode()for value in records]
    output=io.BytesIO();f.filtered(io.BytesIO(b''.join(lines)),output)
    assert output.getvalue()==lines[0]+lines[2]+lines[3]
    assert c.terminal_success(output.getvalue().decode()) is True


@pytest.mark.parametrize('raw',[b'not-json\n',b'[]\n'])
def test_malformed_native_stream_cannot_be_returned_as_success(raw):
    with pytest.raises((ValueError,RuntimeError)):f.filtered(io.BytesIO(raw),io.BytesIO())


def test_raw_update_limit_remains_enforced_even_when_updates_are_dropped(monkeypatch):
    monkeypatch.setattr(f,'RAW_LIMIT',100)
    line=(json.dumps({'type':'message_update','message':'x'*50})+'\n').encode()
    with pytest.raises(RuntimeError,match='exceeds bound'):f.filtered(io.BytesIO(line*3),io.BytesIO())


def test_retained_native_output_limit_is_independent(monkeypatch):
    monkeypatch.setattr(f,'RETAIN_LIMIT',60)
    line=(json.dumps({'type':'agent_end','messages':['x'*40]})+'\n').encode()
    with pytest.raises(RuntimeError,match='256KiB'):f.filtered(io.BytesIO(line),io.BytesIO())


@pytest.mark.parametrize('events',[
    [],[{'type':'agent_end','messages':[{'role':'assistant','stopReason':'stop'}]}],
    [{'type':'turn_end'},{'type':'agent_end','messages':[{'role':'assistant','stopReason':'error'}]}],
    [{'type':'turn_end'},{'type':'error','message':'authored error'},{'type':'agent_end','messages':[{'role':'assistant','stopReason':'stop'}]}],
])
def test_incomplete_or_failed_native_terminal_cannot_pass(events):
    assert c.terminal_success('\n'.join(json.dumps(value)for value in events)) is False


def test_real_authored_native_child_uses_private_home_excludes_operator_and_redacts_output(tmp_path,monkeypatch):
    script=tmp_path/'authored_native.py';script.write_text('import os\nassert "GITHUB_TOKEN"not in os.environ\nassert os.environ["HOME"]!='+repr(str(tmp_path))+'\nprint("synthetic-private-key")\n')
    monkeypatch.setattr(c,'native_binary',lambda:sys.executable)
    monkeypatch.setattr(c,'CONFIG',{'MODEL_BASE_URL':'https://approved.invalid/v1','MODEL_API_KEY':'synthetic-private-key','MODEL':'fixture-model'})
    monkeypatch.setenv('GITHUB_TOKEN','operator-credential')
    result=c.run_native([str(script)],timeout=10,model=False)
    assert result['exit_code']==0 and result['stdout'].strip()=='[REDACTED]'and result['native_completed'] is False
