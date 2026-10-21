"""Fixed controller metadata and local-target refusal, no generated code execution."""
import importlib.util
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('claude_external_controller_controls',Path(__file__).with_name('e2e_test.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def result():return {'exit_code':0,'native_completed':True,'native_version':'2.0.76','cli_sha256':'45b889599096a2fd6911fdd6ac41d59987b58d04de32e61ea5ec01b28fcc6269','protocol':'authored-messages-chat-text-tools','model_calls':1,'native_tool_results':1,'relay_calls':{'completed_responses':1,'failed_responses':0},'stdout':'FIXED_NON_EXECUTABLE_FINAL'}

def test_valid_native_metadata():assert module.final_text(result())=='FIXED_NON_EXECUTABLE_FINAL'

@pytest.mark.parametrize('key,value',[('exit_code',True),('exit_code',1),('native_completed',False),('native_version','other'),('cli_sha256','0'*64),('protocol','chat'),('model_calls',True),('model_calls',0),('native_tool_results',0),('native_tool_results',True),('relay_calls',{'completed_responses':0,'failed_responses':0}),('relay_calls',{'completed_responses':1,'failed_responses':1}),('relay_calls',{'completed_responses':True,'failed_responses':False})])
def test_marker_cannot_replace_original_native_tool_and_delivery_acceptance(key,value):
    data=result();data[key]=value;assert module.final_text(data)==''

def test_model_code_never_runs_on_operator_even_with_remote_flag(monkeypatch):
    monkeypatch.setenv('E2E_RUN_LLM','1');monkeypatch.setenv('E2E_REMOTE_SANDBOX','1');module.RESULTS.clear()
    module.model_check(object(),'/tmp/does-not-exist','http://127.0.0.1:9000')
    assert module.RESULTS==[False]
