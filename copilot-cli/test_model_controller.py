"""Controller regressions reject commentary, native errors and local execution."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('copilot_target_controller',Path(__file__).with_name('e2e_test.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
def test_final_response_is_assistant_content_not_tool_or_prompt_echo():
    assert c.final_text(json.dumps({'type':'tool.execution_start','data':{'content':'ABX_E2E_marker'}}))==''
    assert c.final_text(json.dumps({'type':'assistant.message','data':{'content':'complete'}}))=='complete'
    assert c.final_text('not json')==''
    assert c.final_text(json.dumps({'type':'assistant.message','data':{'content':'complete'}})+'\n'+json.dumps({'type':'session.error'}))==''
def test_real_model_controller_refuses_operator_local_target(monkeypatch):
    monkeypatch.setenv('E2E_RUN_LLM','1');monkeypatch.setenv('E2E_REMOTE_SANDBOX','1');c.RESULTS.clear()
    c.model_check(None,'/tmp','http://127.0.0.1:9000');assert c.RESULTS==[False]
