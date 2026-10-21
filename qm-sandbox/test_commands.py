"""Authored public wrapper boundaries; no native QM or model runs on operator."""
import importlib.util
from pathlib import Path
import sys
import json
import pytest


def load(directory):
    file=Path(__file__).parents[1]/directory/'commands.py'
    spec=importlib.util.spec_from_file_location('qm_wrapper_'+directory.replace('-','_'),file)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('name,value',[('command_timeout',True),('command_timeout',0),('command_timeout',121),('command',''),('command','x\0y')])
def test_backend_invalid_command_never_reaches_runtime(monkeypatch,name,value):
    module=load('qm-sandbox')
    monkeypatch.setattr(module,'invoke',lambda *a,**k:pytest.fail('invalid command reached runtime'))
    parameters={'command':'fixed authored request',name:value}
    with pytest.raises(ValueError):module.backend_exec(**parameters)


@pytest.mark.parametrize('name,value',[('command_timeout',True),('command_timeout',0),('command_timeout',601),('prompt',''),('prompt','x\0y')])
def test_model_invalid_arguments_never_read_credentials(monkeypatch,name,value):
    module=load('qm')
    monkeypatch.setattr(module,'model_settings',lambda:pytest.fail('invalid model request read settings'))
    parameters={'prompt':'fixed authored request',name:value}
    with pytest.raises(ValueError):module.qm(**parameters)


@pytest.mark.parametrize('base',['https://example.invalid','http://localhost:9000','http://user@127.0.0.1:9000','http://127.0.0.1:9000?token=bad','http://127.0.0.1:9000/path','http://127.0.0.1:bad'])
def test_sdk_base_refuses_unintended_route_before_native_call(monkeypatch,base):
    module=load('qm-sandbox');monkeypatch.setattr(module,'SDK_BASE',base)
    with pytest.raises(ValueError):module.sdk_settings()


@pytest.mark.parametrize('base',['https://@example.invalid','https://user:pass@example.invalid','https://example.invalid?key=bad','https://example.invalid#fragment','http://public.invalid','https://example.invalid:bad'])
def test_approved_model_base_is_explicit_and_bounded(monkeypatch,base):
    module=load('qm');monkeypatch.setattr(module,'MODEL',{'MODEL_BASE_URL':base,'MODEL_API_KEY':'synthetic-key','MODEL':'fixture-model'})
    with pytest.raises(ValueError):module.model_settings()


def test_public_file_symlink_escape_cannot_modify_caller_data(tmp_path,monkeypatch):
    module=load('qm-sandbox');root=tmp_path/'project';root.mkdir();outside=tmp_path/'caller.txt';outside.write_text('preserve');(root/'escape').symlink_to(outside)
    monkeypatch.setattr(module,'ROOT',root);monkeypatch.setattr(module,'invoke',lambda *a,**k:pytest.fail('escaped path invoked backend'))
    with pytest.raises(ValueError):module.backend_file('write','escape','changed')
    assert outside.read_text()=='preserve'


def test_real_authored_worker_gets_settings_only_on_anonymous_stdin(tmp_path,monkeypatch):
    module=load('qm');worker=tmp_path/'authored.py'
    worker.write_text("import json,os,sys\nvalue=json.load(sys.stdin)\nassert value['settings']['key']=='synthetic-only-key'\nassert 'synthetic-only-key' not in ' '.join(sys.argv)\nassert 'OPENAI_API_KEY' not in os.environ and 'ABX_SERVER_TOKEN' not in os.environ\nprint(json.dumps({'anonymous_request':True,'private_home':os.environ['HOME']!=str(value['caller_home'])}))\n")
    monkeypatch.setattr(module,'runtime',lambda:(sys.executable,str(worker)))
    monkeypatch.setenv('OPENAI_API_KEY','synthetic-operator-key');monkeypatch.setenv('ABX_SERVER_TOKEN','synthetic-server-key')
    result=module.invoke('version',{'settings':{'key':'synthetic-only-key'},'caller_home':str(tmp_path)},10)
    assert result=={'anonymous_request':True,'private_home':True}


def test_returned_nested_text_redacts_native_configuration_and_escaped_values(monkeypatch):
    module=load('qm');monkeypatch.setattr(module,'MODEL',{'MODEL_API_KEY':'synthetic"key','MODEL_BASE_URL':'https://approved.invalid','MODEL':'fixture-model'})
    monkeypatch.setattr(module,'SDK_TOKEN','synthetic-sdk-token')
    result=module.redact({'stdout':['synthetic"key '+json.dumps('synthetic"key')[1:-1]+' synthetic-sdk-token https://approved.invalid']})
    assert result=={'stdout':['[REDACTED] [REDACTED] [REDACTED] [REDACTED]']}


def test_failed_authored_worker_exposes_only_fixed_phase_and_validated_counts(tmp_path,monkeypatch):
    module=load('qm');worker=tmp_path/'authored_failure.py'
    diagnostic={'error_type':'ImportError','native_stage':'qm_harness_import','error_code':'ERR_MODULE_NOT_FOUND','missing_module':'safe-public-package','native_counters':{'sdk_shell':2,'private':'SYNTHETIC_PRIVATE_BODY'},'message':'SYNTHETIC_PRIVATE_BODY /private/owned/path'}
    worker.write_text('import json\nprint('+repr(json.dumps(diagnostic))+')\nraise SystemExit(1)\n')
    monkeypatch.setattr(module,'runtime',lambda:(sys.executable,str(worker)))
    with pytest.raises(RuntimeError)as error:module.invoke('version',{},10)
    text=str(error.value)
    assert 'qm_harness_import'in text and 'ERR_MODULE_NOT_FOUND'in text and 'sdk_shell=2'in text
    assert 'SYNTHETIC_PRIVATE_BODY'not in text and '/private/owned/path'not in text
