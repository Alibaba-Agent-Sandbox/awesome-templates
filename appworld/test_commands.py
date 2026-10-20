"""Authored wrapper boundaries; no AppWorld/model runtime executes on operator."""
import importlib.util
import json
import sys
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('appworld_boundary_tests',Path(__file__).with_name('commands.py'))
c=importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


@pytest.mark.parametrize('task',['../other','x'*65,'task.invalid','bad\x00task',True,12])
def test_invalid_task_never_reaches_original_engine(monkeypatch,task):
    monkeypatch.setattr(c,'_invoke',lambda *a,**k:pytest.fail('invalid task invoked native engine'))
    with pytest.raises(ValueError):
        c.appworld_run(task=task)


@pytest.mark.parametrize('name,value',[('max_steps',True),('max_steps',0),('max_steps',41),('command_timeout',True),('command_timeout',29),('command_timeout',901)])
def test_bounds_fail_before_credentials_or_mutation(monkeypatch,name,value):
    monkeypatch.setattr(c,'_config',lambda:pytest.fail('invalid bound read credentials'))
    with pytest.raises(ValueError):
        c.appworld_run(**{name:value})


@pytest.mark.parametrize('base',['https://@example.invalid','https://user:pass@example.invalid','https://example.invalid?key=secret','https://example.invalid#fragment','http://public.invalid','https://example.invalid:bad'])
def test_explicit_model_base_rejects_unsafe_route(monkeypatch,base):
    monkeypatch.setattr(c,'_CONFIG',{'MODEL_BASE_URL':base,'MODEL_API_KEY':'synthetic-only-key','MODEL':'fixture-model'})
    with pytest.raises(ValueError):
        c._config()


def test_private_environment_has_no_operator_or_model_credentials(tmp_path,monkeypatch):
    for name in ['OPENAI_API_KEY','GITHUB_TOKEN','ALICLOUD_ACCESS_KEY_SECRET','APPWORLD_MODEL_API_KEY','PYTHONPATH']:
        monkeypatch.setenv(name,'operator-value')
    env=c._environment(tmp_path)
    assert not any(name in env for name in ['OPENAI_API_KEY','GITHUB_TOKEN','ALICLOUD_ACCESS_KEY_SECRET','APPWORLD_MODEL_API_KEY','PYTHONPATH'])
    assert env['APPWORLD_ROOT']==str(tmp_path/'world')
    assert env['HOME']==str(tmp_path)


def test_artifact_symlink_escape_never_reaches_decryption(tmp_path,monkeypatch):
    root=tmp_path/'workspace';root.mkdir()
    outside=tmp_path/'unrelated.bundle';outside.write_bytes(b'caller-owned')
    (root/'escape.bundle').symlink_to(outside)
    monkeypatch.setattr(c,'_ROOT',root)
    monkeypatch.setattr(c,'_invoke',lambda *a,**k:pytest.fail('escaped native artifact invoked'))
    with pytest.raises(ValueError):
        c.appworld_verify_artifact('escape.bundle')
    assert outside.read_bytes()==b'caller-owned'


def test_failed_native_run_removes_only_its_new_result_directory(tmp_path,monkeypatch):
    marker=tmp_path/'caller.txt';marker.write_text('preserve')
    monkeypatch.setattr(c,'_ROOT',tmp_path)
    monkeypatch.setattr(c,'_config',lambda:{'key':'synthetic','base':'http://127.0.0.1','model':'fixture'})
    def fail(*args):
        raise RuntimeError('authored native failure')
    monkeypatch.setattr(c,'_invoke',fail)
    with pytest.raises(RuntimeError):
        c.appworld_run()
    assert list(tmp_path.iterdir())==[marker]


def test_real_authored_subprocess_receives_request_only_on_anonymous_stdin(tmp_path,monkeypatch):
    worker=tmp_path/'authored.py'
    worker.write_text("import json,os,sys\nvalue=json.load(sys.stdin)\nassert value['settings']['key']=='synthetic-secret'\nassert 'synthetic-secret' not in ' '.join(sys.argv)\nassert 'OPENAI_API_KEY' not in os.environ\nprint(json.dumps({'anonymous_input':True,'private_home':os.environ['HOME']!=str(value.get('caller_home',''))}))\n")
    monkeypatch.setattr(c,'_runtime',lambda:(sys.executable,str(worker)))
    monkeypatch.setenv('OPENAI_API_KEY','operator-secret')
    result=c._invoke('version',{'settings':{'key':'synthetic-secret'}},10)
    assert result=={'anonymous_input':True,'private_home':True}


@pytest.mark.parametrize('kind',['PermissionError','ImportError','Error','JSONDecodeError','InvalidToken'])
def test_real_worker_error_reports_only_validated_class_without_private_message(tmp_path,monkeypatch,kind):
    worker=tmp_path/'authored_failure.py'
    diagnostic={'error_type':kind,'native_stage':'upstream','message':'SYNTHETIC_PRIVATE_VALUE /private/owned/path'}
    worker.write_text('import sys\nprint('+repr(json.dumps(diagnostic))+',file=sys.stderr)\nraise SystemExit(1)\n')
    monkeypatch.setattr(c,'_runtime',lambda:(sys.executable,str(worker)))
    with pytest.raises(RuntimeError) as error:
        c._invoke('smoke',{},10)
    text=str(error.value)
    assert 'upstream ('+kind+')' in text and 'native_exit_code=1' in text
    assert 'SYNTHETIC_PRIVATE_VALUE' not in text and '/private/owned/path' not in text


def test_early_native_traceback_exposes_only_class(tmp_path,monkeypatch):
    worker=tmp_path/'early_failure.py'
    worker.write_text('import sys\nprint("ImportError: SYNTHETIC_PRIVATE_VALUE /private/owned/path",file=sys.stderr)\nraise SystemExit(1)\n')
    monkeypatch.setattr(c,'_runtime',lambda:(sys.executable,str(worker)))
    with pytest.raises(RuntimeError) as error:
        c._invoke('smoke',{},10)
    text=str(error.value)
    assert 'entrypoint (ImportError)' in text and 'SYNTHETIC_PRIVATE_VALUE' not in text and '/private/owned/path' not in text


def test_original_installer_can_write_only_the_owned_copy_of_readonly_source(tmp_path):
    spec=importlib.util.spec_from_file_location('appworld_private_copy_tests',Path(__file__).with_name('worker.py'))
    worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
    original=tmp_path/'original';original.mkdir()
    apps=original/'apps';apps.mkdir()
    source=apps/'public.py';source.write_text('original unchanged')
    source.chmod(0o444);apps.chmod(0o555);original.chmod(0o555)
    owned=tmp_path/'owned';owned.mkdir(mode=0o700)
    try:
        package=worker.copy_private_package(original,owned)
        (package/'apps/private_installed.py').write_text('authored private install fixture')
        assert (package/'apps/public.py').read_text()=='original unchanged'
        assert package.stat().st_mode&0o777==0o700
        assert (package/'apps/public.py').stat().st_mode&0o777==0o600
        assert source.stat().st_mode&0o777==0o444 and not (apps/'private_installed.py').exists()
    finally:
        original.chmod(0o700);apps.chmod(0o700);source.chmod(0o600)


def test_native_diagnostic_survives_trailing_library_shutdown_stderr(tmp_path,monkeypatch):
    worker=tmp_path/'late_stderr.py'
    diagnostic={'error_type':'NativeIncomplete','native_stage':'native_completion_check','native_counters':{'model_steps':40,'bridge_api_calls':3,'private_body':'SYNTHETIC_PRIVATE_VALUE'}}
    worker.write_text('import sys\nprint('+repr('ABX_APPWORLD_FAILURE '+json.dumps(diagnostic))+',file=sys.stderr)\nprint("Unrelated native shutdown text: SYNTHETIC_PRIVATE_VALUE",file=sys.stderr)\nraise SystemExit(1)\n')
    monkeypatch.setattr(c,'_runtime',lambda:(sys.executable,str(worker)))
    with pytest.raises(RuntimeError) as error:
        c._invoke('run',{},10)
    text=str(error.value)
    assert 'native_completion_check (NativeIncomplete)' in text and 'model_steps=40' in text and 'bridge_api_calls=3' in text
    assert 'SYNTHETIC_PRIVATE_VALUE' not in text and 'private_body' not in text


def test_compatible_response_without_transport_id_still_requires_real_choice():
    from types import SimpleNamespace as NS
    spec=importlib.util.spec_from_file_location('appworld_response_tests',Path(__file__).with_name('worker.py'))
    worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
    worker.RUN_OBSERVATION={'model_steps':0,'empty_model_responses':0}
    calls=[]
    def create(**kwargs):
        calls.append(kwargs)
        return NS(id=None,choices=[NS(message=NS(content='fixed synthetic response',tool_calls=[]))])
    client=NS(chat=NS(completions=NS(create=create)))
    response=worker.request_completion(client,{'model':'fixture-model'},[],[])
    assert response.id is None and response.choices[0].message.content=='fixed synthetic response'
    assert len(calls)==1 and calls[0]['model']=='fixture-model'
    assert worker.RUN_OBSERVATION=={'model_steps':1,'empty_model_responses':0}


def test_empty_native_choices_have_a_strict_total_retry_budget():
    from types import SimpleNamespace as NS
    spec=importlib.util.spec_from_file_location('appworld_empty_response_tests',Path(__file__).with_name('worker.py'))
    worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
    worker.RUN_OBSERVATION={'model_steps':0,'empty_model_responses':0}
    calls=[]
    def create(**kwargs):
        calls.append(kwargs)
        return NS(id='synthetic-id',choices=[])
    client=NS(chat=NS(completions=NS(create=create)))
    with pytest.raises(worker.NativeIncomplete):
        worker.request_completion(client,{'model':'fixture-model'},[],[])
    assert len(calls)==3
    assert worker.RUN_OBSERVATION=={'model_steps':3,'empty_model_responses':3}
