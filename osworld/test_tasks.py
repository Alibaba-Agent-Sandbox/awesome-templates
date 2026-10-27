"""Actual pinned evaluator definitions and strict task capability boundaries."""
import hashlib
import importlib.util
import json
from pathlib import Path
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


def test_initialization_diagnostics_only_expose_fixed_stage_and_exception_class(monkeypatch,tmp_path):
    def fail(self):
        self.stage='browser-location'
        raise RuntimeError('synthetic-private-browser-path')
    monkeypatch.setattr(runtime.Desktop,'start',fail)
    with pytest.raises(runtime.InitializationError) as error:runtime.Desktop(tmp_path)
    assert error.value.stage=='browser-location' and error.value.cause=='RuntimeError'
    assert 'synthetic-private' not in str(error.value)


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


def test_geometry_preserves_a_viewport_distinct_from_the_desktop():
    observed={'screen_width':1024,'screen_height':768,'outer_width':1024,'outer_height':768,
              'viewport_width':1024,'viewport_height':680,'content_x':0,'content_y':88}
    desktop=runtime.Desktop.__new__(runtime.Desktop)
    desktop.page=SimpleNamespace(evaluate=lambda expression:observed.copy())
    assert desktop.geometry()==observed
    for invalid in ('private-path',float('nan'),float('inf'),-1):
        observed['viewport_height']=invalid
        with pytest.raises(RuntimeError,match='invalid browser geometry'):desktop.geometry()


def test_unchanged_original_xml_walker_keeps_children_after_empty_native_attributes():
    import ast,logging
    import lxml.etree
    source=ast.parse((runtime.SOURCE/'main.py').read_text())
    node=next(n for n in source.body if isinstance(n,ast.FunctionDef)and n.name=='_create_atspi_node')
    ns=next(ast.literal_eval(n.value)['ubuntu']for n in source.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='_accessibility_ns_map'for t in n.targets))
    scope={'lxml':__import__('lxml'),'_accessibility_ns_map_ubuntu':ns,'MAX_DEPTH':50,'MAX_WIDTH':1024,'logger':logging.getLogger('original-walker-regression')}
    module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),node],type_ignores=[])
    exec(compile(ast.fix_missing_locations(module),'unchanged-original-walker','exec'),scope)
    class Accessible:
        def __init__(self,name,attributes,children=()):self.name,self.attributes,self.children=name,attributes,children
        def getState(self):return SimpleNamespace(get_states=lambda:[])
        def get_attributes(self):
            if isinstance(self.attributes,Exception):raise self.attributes
            return self.attributes
        def getRoleName(self):return 'document web'if self.children else'paragraph'
        def __iter__(self):return iter(self.children)
        def __getattr__(self,name):
            if name.startswith('query'):
                def unavailable():raise NotImplementedError
                return unavailable
            raise AttributeError(name)
    values={'tag':'p'};child=Accessible('Awaiting amount',values);parent=Accessible('Expense entry',None,[child])
    with pytest.raises(AttributeError,match='items'):scope['_create_atspi_node'](parent)
    runtime.normalize_nullable_attributes(Accessible)
    tree=scope['_create_atspi_node'](parent)
    assert tree.tag=='document-web'and tree.xpath('.//paragraph/@name')==['Awaiting amount']
    assert child.get_attributes()is values
    with pytest.raises(RuntimeError,match='native refusal'):Accessible('refused',RuntimeError('native refusal')).get_attributes()


def test_real_observer_subprocess_is_fresh_and_filters_host_credentials(tmp_path,monkeypatch):
    import os
    root=tmp_path/'upstream';root.mkdir()
    (root/'main.py').write_text("import os\ncount=0\nclass Accessible:\n def get_attributes(self):return None\nclass Response:\n status_code=200\n def get_json(self):\n  global count;count+=1\n  return {'AT':f\"<desktop pid='{os.getpid()}' count='{count}' secret_present='{str('OPENAI_API_KEY' in os.environ)}'/>\"}\nclass App:\n def test_client(self):return self\n def get(self,path):return Response()\napp=App()\n")
    monkeypatch.setenv('OPENAI_API_KEY','synthetic-not-for-native-observer')
    desktop=runtime.Desktop.__new__(runtime.Desktop);desktop.directory=tmp_path
    import xml.etree.ElementTree as ET
    first,second=[ET.fromstring(desktop.tree())for _ in range(2)]
    assert first.attrib['pid']!=second.attrib['pid']
    assert first.attrib['count']==second.attrib['count']=='1'
    assert first.attrib['secret_present']==second.attrib['secret_present']=='False'


def test_observer_error_does_not_reflect_upstream_private_details(tmp_path):
    root=tmp_path/'upstream';root.mkdir();(root/'main.py').write_text("raise RuntimeError('synthetic-private-native-task-content')\n")
    desktop=runtime.Desktop.__new__(runtime.Desktop);desktop.directory=tmp_path
    with pytest.raises(RuntimeError,match='native accessibility observation failed')as error:desktop.tree()
    assert 'synthetic-private'not in str(error.value)
