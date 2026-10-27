"""Original native QM completion metadata; fixed authored fixtures are not model proof."""
import importlib.util
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('qm_terminal_controls',Path(__file__).with_name('e2e_test.py'))
controller=importlib.util.module_from_spec(spec);spec.loader.exec_module(controller)


def fixture():
    return {'exit_code':0,'native_completed':True,'qm_version':'0.1.0','node_version':'24.16.0','sdk_version':'0.1.0',
            'source_commit':'deef9b8b1e2b85bd4166dd833604bb31bcb8e255','model_calls':2,'native_tool_calls':2,
            'native_tool_results':2,'sdk_calls':{'shell':3},'stopped':False,'pending_approvals':0,'stdout':'FRESH_MARKER'}


def test_original_native_completion_metadata_with_real_tool_and_sdk_counts():
    assert controller.final_text(fixture())=='FRESH_MARKER'


@pytest.mark.parametrize('key,value',[('exit_code',1),('exit_code',False),('native_completed',False),('qm_version','other'),('model_calls',0),('model_calls',True),('native_tool_calls',0),('native_tool_results',0),('stopped',True),('pending_approvals',1),('pending_approvals',False),('stdout','')])
def test_marker_without_actual_native_completion_is_rejected(key,value):
    result=fixture();result[key]=value
    assert controller.final_text(result)==''


def test_native_tools_without_completed_sdk_operations_are_rejected():
    result=fixture();result['sdk_calls']={'shell':True}
    assert controller.final_text(result)==''
