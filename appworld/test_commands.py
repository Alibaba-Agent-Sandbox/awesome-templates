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
