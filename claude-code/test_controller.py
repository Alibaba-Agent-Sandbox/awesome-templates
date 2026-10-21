"""Fixed controller metadata and local-target refusal, no generated code execution."""
import importlib.util
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('claude_external_controller_controls',Path(__file__).with_name('byok_e2e_test.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def result():return {'exit_code':0,'native_completed':True,'native_version':'2.0.76','cli_sha256':'45b889599096a2fd6911fdd6ac41d59987b58d04de32e61ea5ec01b28fcc6269','protocol':'authored-messages-chat-text-tools','model_calls':1,'native_tool_results':1,'relay_calls':{'completed_responses':1,'failed_responses':0},'stdout':'FIXED_NON_EXECUTABLE_FINAL'}

def test_valid_native_metadata():assert module.final_text(result())=='FIXED_NON_EXECUTABLE_FINAL'

@pytest.mark.parametrize('key,value',[('exit_code',True),('exit_code',1),('native_completed',False),('native_version','other'),('cli_sha256','0'*64),('protocol','chat'),('model_calls',True),('model_calls',0),('native_tool_results',0),('native_tool_results',True),('relay_calls',{'completed_responses':0,'failed_responses':0}),('relay_calls',{'completed_responses':1,'failed_responses':1}),('relay_calls',{'completed_responses':True,'failed_responses':False})])
def test_marker_cannot_replace_original_native_tool_and_delivery_acceptance(key,value):
    data=result();data[key]=value;assert module.final_text(data)==''

def test_model_code_never_runs_on_operator_even_with_remote_flag(monkeypatch):
    monkeypatch.setenv('E2E_RUN_LLM','1');monkeypatch.setenv('E2E_REMOTE_SANDBOX','1');module.RESULTS.clear()
    module.model_check(object(),'/tmp/does-not-exist','http://127.0.0.1:9000')
    assert module.RESULTS==[False]


def test_failure_stage_counters_are_bounded_metadata_only():
    assert module.safe_diagnostic('native_subtype=success; failure_counts={"upstream_open_http_400": 2}; upstream_status=200')=={'native_subtype':'success','upstream_status':200,'failure_counts':{'upstream_open_http_400':2}}
    assert 'failure_counts'not in module.safe_diagnostic('failure_counts={"PRIVATE/URL": 2}')


def test_actual_typed_failure_stage_names_remain_visible():
    assert module.safe_diagnostic('failure_counts={"reply_shape_ValueError": 1, "native_stream_BrokenPipeError": 1}')['failure_counts']=={'reply_shape_ValueError':1,'native_stream_BrokenPipeError':1}


@pytest.mark.parametrize('required',[False,True])
def test_optional_source_profile_skip_does_not_relax_required_native_gate(monkeypatch,required):
    import httpx
    original=httpx.Client
    names={'claude','claude_byok','claude_version','claude_setup_check','claude_native_check'}
    def handle(request):
        path=request.url.path
        if path=='/health':return httpx.Response(200,json={'status':'ok'})
        if path=='/commands':return httpx.Response(200,json={'commands':[{'name':n}for n in names]})
        if path=='/commands/claude_setup_check':return httpx.Response(200,json={'result':{'mode':'original-claude-explicit-chat-adapter'}})
        if path=='/commands/claude_version':return httpx.Response(200,json={'result':'2.0.76 (Claude Code)'})
        if path=='/commands/claude_native_check':return httpx.Response(500,json={'error':'exact installed native profile absent'})
        return httpx.Response(400,json={'error':'invalid request'})
    monkeypatch.setattr(module.httpx,'Client',lambda **kwargs:original(transport=httpx.MockTransport(handle),**kwargs))
    monkeypatch.setenv('E2E_REQUIRE_CLI','1'if required else'0');monkeypatch.setenv('E2E_RUN_LLM','0');monkeypatch.setenv('E2E_REQUIRE_LLM','0');module.RESULTS.clear()
    assert module.main()==int(required)
