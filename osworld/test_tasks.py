"""Actual pinned evaluator definitions and strict task capability boundaries."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

spec=importlib.util.spec_from_file_location('osworld_test_runtime',Path(__file__).with_name('runtime.py'))
runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)


def task():
    return {'id':'test','snapshot':'chrome','config':[], 'evaluator':{'func':'check_include_exclude','result':{'type':'accessibility_tree'},'expected':{'type':'rule','rules':{'include':['Completed task'],'exclude':['Awaiting input']}}}}


def validate(monkeypatch,tmp_path,value):
    monkeypatch.setenv('WORKSPACE',str(tmp_path));p=tmp_path/'task.json';p.write_text(json.dumps(value));return runtime.task_configuration(str(p))


def test_pinned_vendored_files_match_recorded_official_source_sha256():
    manifest=json.loads((runtime.SOURCE/'source.json').read_text())
    assert manifest['commit']=='b138d348256078fa634fc3b73567a7337c793e6b'
    for name,data in manifest['files'].items():
        assert hashlib.sha256((runtime.SOURCE/name).read_bytes()).hexdigest()==data['sha256']


def test_actual_upstream_metric_observes_state_and_does_not_read_submission_score(monkeypatch,tmp_path,capsys):
    value=validate(monkeypatch,tmp_path,task())
    metric=runtime.load_functions('metrics_general.py',('check_include_exclude','exact_match'))
    getters=runtime.load_functions('getters_misc.py',('get_rule','get_accessibility_tree'))
    expected=getters['get_rule'](None,value['evaluator']['expected'])
    for actual,score in [('Awaiting input',0.0),('Completed task',1.0),('Completed task Awaiting input',0.0)]:
        env=SimpleNamespace(controller=SimpleNamespace(get_accessibility_tree=lambda:actual))
        assert metric['check_include_exclude'](getters['get_accessibility_tree'](env),expected)==score
    assert metric['exact_match']('actual',{'expected':'wanted'})==0
    assert metric['exact_match']('wanted',{'expected':'wanted'})==1


@pytest.mark.parametrize('kind',['launch','execute','download','vm_snapshot','chrome_inject_js','Office'])
def test_unsupported_setup_fails_whole_task_before_any_side_effect(monkeypatch,tmp_path,kind):
    value=task();value['config']=[{'type':'sleep','parameters':{'seconds':0}},{'type':kind,'parameters':{}}]
    with pytest.raises(ValueError,match='unsupported setup'):validate(monkeypatch,tmp_path,value)


@pytest.mark.parametrize('change',[
 lambda t:t.update(snapshot='libreoffice'),lambda t:t.update(proxy=True),lambda t:t.update(fixed_ip=True),
 lambda t:t['evaluator'].update(postconfig=[]),lambda t:t['evaluator'].update(func='infeasible'),
 lambda t:t['evaluator'].update(result={'type':'vm_command_line','command':['env']}),
 lambda t:t['evaluator']['expected'].update(type='cloud_file'),
 lambda t:t['evaluator']['expected'].update(rules={'include':[]}),
 lambda t:t.update(config=[{'type':'sleep','parameters':{'seconds':999}}]),
 lambda t:t.update(config=[{'type':'chrome_open_tabs','parameters':{'urls_to_open':['https://user:secret@example.invalid']}}]),
])
def test_unsupported_evaluator_or_task_requirements_are_errors(monkeypatch,tmp_path,change):
    value=task();change(value)
    with pytest.raises(ValueError):validate(monkeypatch,tmp_path,value)


def test_supported_official_task_shape_and_local_file_boundary(monkeypatch,tmp_path):
    page=tmp_path/'task.html';page.write_text('<title>task</title>')
    value=task();value['config']=[{'type':'chrome_open_tabs','parameters':{'urls_to_open':[page.as_uri()]}},{'type':'sleep','parameters':{'seconds':.01}}]
    assert validate(monkeypatch,tmp_path,value)==value
    outside=tmp_path.parent/'outside.html';outside.write_text('outside')
    with pytest.raises(ValueError):runtime.validate_url(outside.as_uri())
