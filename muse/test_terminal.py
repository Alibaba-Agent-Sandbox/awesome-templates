"""Authored metadata fixtures only; never original native/model execution on operator."""
import importlib.util,json
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('muse_terminal_controls',Path(__file__).with_name('filter_native.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def fixture():
    common={'command_id':'owned-command','run_stream':{'id':'owned-command','kind':'run'}}
    def event(kind,body):return {'schema_version':1,'payload_type':kind,'payload':{**common,**body}}
    return [event('run.model.configured',{'model_id':'unit-model','provider_id':'meta'}),event('tool.result',{'call_id':'owned-tool','text':'fixed non-executable fixture'}),event('run.usage',{'calls':1,'completed_calls':1,'cancelled_calls':0,'failed_calls':0,'children_included':False}),event('run.terminal.completed',{'terminal':'completed','reason':None,'text':'FIXED_FINAL'})]


def parse(rows,code=0):return module.completed('\n'.join(json.dumps(v)for v in rows),code,'unit-model')

def test_genuine_shaped_correlated_terminal_metadata():
    assert parse(fixture())=={'native_completed':True,'model_calls':1,'native_tool_results':1,'stdout':'FIXED_FINAL'}

@pytest.mark.parametrize('index,key,value',[(0,'model_id','other'),(0,'provider_id','echo'),(2,'calls',True),(2,'completed_calls',True),(2,'completed_calls',0),(2,'failed_calls',1),(2,'cancelled_calls',1),(2,'children_included',True),(3,'text',''),(3,'terminal','cancelled'),(3,'reason','max_model_steps')])
def test_false_terminal_cannot_be_accepted(index,key,value):
    rows=fixture();rows[index]['payload'][key]=value;assert parse(rows)['native_completed']is False

@pytest.mark.parametrize('mode',['missing','duplicate','unrelated_usage','unrelated_model','nonzero','truncated'])
def test_exit_or_cross_run_markers_cannot_qualify(mode):
    rows=fixture();code=0
    if mode=='missing':rows.pop()
    elif mode=='duplicate':rows.append(rows[-1])
    elif mode=='unrelated_usage':rows[2]['payload']['command_id']='other'
    elif mode=='unrelated_model':rows[0]['payload']['command_id']='other'
    elif mode=='nonzero':code=1
    else:rows.pop(2)
    assert parse(rows,code)['native_completed']is False

def test_malformed_native_records_refused():
    with pytest.raises(ValueError):module.completed('not-json',0,'unit-model')
