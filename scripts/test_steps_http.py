"""Native step preparation must use the existing full current launch consumer."""
from argparse import Namespace
import json
from pathlib import Path
import pytest
import run_steps_e2e as steps
import run_ci_image_e2e as current
from public_launch_e2e import CLI


def config():
    return Namespace(region='cn-hangzhou',base_tag='v0.0.49',base_path=None,
                     asset_transport='direct',timeout=60)


@pytest.fixture
def prepared(tmp_path,monkeypatch):
    source=tmp_path/'example';source.mkdir()
    original={'name':'example','version':'1.0.1','start_cmd':'original start','ready_cmd':'original ready',
              'services':{'app':{'port':9000}},'env':{'APP_SETTING':'value'}}
    import yaml
    (source/'template.yaml').write_text(yaml.safe_dump(original))
    monkeypatch.setattr(steps,'ROOT',tmp_path)
    monkeypatch.setattr(current,'controller_missing_imports',lambda _:[])
    monkeypatch.setattr(steps,'prepare',lambda *a,**k:({**original,'build':{'steps':[]}}, {'build_mode':'steps'}))
    resources=[];calls=[]
    def cli(self,args,*a,**kwargs):
        calls.append((args,kwargs))
        if args[-1:] == ['--help']:
            assert kwargs['native'] is True and kwargs['json_output'] is False
            return '--build --alias --generation --start-cmd --ready-cmd'
        if args[:2]==['template','list']:
            return [{'Name':self.env.get('unused',''), 'TemplateID':x} for x in resources]
        if args[:2]==['template','deploy']:
            assert kwargs['native'] is True
            stage=Path(args[2]);staged=yaml.safe_load((stage/'template.yaml').read_text())
            assert 'start_cmd' not in staged and 'ready_cmd' not in staged
            assert args[args.index('--start-cmd')+1]==''
            assert args[args.index('--ready-cmd')+1]==''
            resources.append('owned-template');return {'TemplateID':'owned-template'}
        if args[:2]==['template','info']:
            if args[2] in resources:return {'status':{'state':'ready'}}
            from public_launch_e2e import CLIError
            raise CLIError('template',4,json.dumps({'code':'E2001','message':'owned template not found'}))
        if args[:2]==['template','delete']:
            assert kwargs['native'] is True
            resources.remove(args[2]);return {}
        pytest.fail('unexpected CLI operation '+str(args))
    monkeypatch.setattr(CLI,'run',cli)
    monkeypatch.setattr(current,'exact_templates',lambda cli,alias:list(resources))
    monkeypatch.setattr(current,'wait_ready',lambda *a:None)
    return source,original,resources,calls


def test_prepare_then_existing_current_launch_and_independent_template_cleanup(prepared,monkeypatch):
    source,original,resources,calls=prepared
    async def exercise(selected,reference,private,report,http,journal,*,runtime_env):
        assert selected==source and reference=='owned-template' and http is True
        import yaml
        assert yaml.safe_load((source/'template.yaml').read_text())==original
        assert json.loads(journal.read_text())['template_id']=='owned-template'
        assert runtime_env==original['env']
        report.update(application_result='PASS',cleanup_verified=True,
                      commands=[{'name':'hello','via':via,'ok':True} for via in ['cli','sdk','host-http']],
                      http_acceptance={'passed':True})
    monkeypatch.setattr(current,'exercise',exercise)
    report=steps.run_one('example',config())
    assert report['passed'] and report['template_cleanup_verified'] and not resources
    assert report['command_calls']==3
    assert not any(args[:1]==['create'] for args,_ in calls)


def test_current_controller_failure_cannot_publish_pass_but_still_cleans(prepared,monkeypatch):
    _,_,resources,_=prepared
    async def failed(*args,**kwargs):
        args[3].update(cleanup_verified=True)
        raise RuntimeError('controlled controller failure')
    monkeypatch.setattr(current,'exercise',failed)
    report=steps.run_one('example',config())
    assert not report['passed'] and report['template_cleanup_verified'] and not resources


def test_missing_controller_stops_before_native_write(prepared,monkeypatch):
    _,_,resources,calls=prepared
    monkeypatch.setattr(current,'controller_missing_imports',lambda _:['missing_dependency'])
    report=steps.run_one('example',config())
    assert not report['passed'] and not report['runtime_attempted'] and not resources and not calls


def test_uncertain_template_cleanup_cannot_become_acceptance(prepared,monkeypatch):
    _,_,resources,_=prepared
    async def exercise(*args,**kwargs):args[3].update(application_result='PASS',cleanup_verified=True,commands=[])
    monkeypatch.setattr(current,'exercise',exercise)
    original=CLI.run
    def reject(self,args,*a,**k):
        if args[:2]==['template','delete']:raise RuntimeError('controlled delete failure')
        return original(self,args,*a,**k)
    monkeypatch.setattr(CLI,'run',reject)
    report=steps.run_one('example',config())
    assert not report['passed'] and not report['template_cleanup_verified'] and resources==['owned-template']


def test_known_template_is_deleted_even_if_inventory_temporarily_omits_it(prepared,monkeypatch):
    _,_,resources,calls=prepared
    monkeypatch.setattr(current,'exact_templates',lambda *args:[])
    async def exercise(*args,**kwargs):
        args[3].update(application_result='PASS',cleanup_verified=True,commands=[],http_acceptance={'passed':True})
    monkeypatch.setattr(current,'exercise',exercise)
    report=steps.run_one('example',config())
    assert report['passed'] and not resources
    assert any(args[:3]==['template','delete','owned-template'] for args,_ in calls)


def test_unknown_owned_cleanup_stops_the_existing_serial_selection(monkeypatch):
    import sys
    monkeypatch.setattr(sys,'argv',['run_steps_e2e.py','--all'])
    monkeypatch.setattr(steps,'catalog_names',lambda:['first','second'])
    calls=[]
    def run(name,args):
        calls.append(name)
        return {'passed':False,'unresolved_owned_cleanup':True}
    monkeypatch.setattr(steps,'run_one',run)
    assert steps.main()==1 and calls==['first']


def test_independently_cleaned_failure_does_not_hide_later_templates(monkeypatch):
    import sys
    monkeypatch.setattr(sys,'argv',['run_steps_e2e.py','first','second'])
    monkeypatch.setattr(steps,'catalog_names',lambda:['first','second'])
    calls=[]
    def run(name,args):
        calls.append(name)
        return {'passed':name=='second','unresolved_owned_cleanup':False}
    monkeypatch.setattr(steps,'run_one',run)
    assert steps.main()==1 and calls==['first','second']


def test_lost_registration_response_and_empty_inventory_remain_uncertain(prepared,monkeypatch):
    _,_,resources,_=prepared
    original=CLI.run;stages=[]
    def uncertain(self,args,*a,**k):
        if args[:2]==['template','deploy'] and args[-1:]!=['--help']:
            stages.append(Path(args[2]))
            raise TimeoutError('controlled lost registration response')
        return original(self,args,*a,**k)
    monkeypatch.setattr(CLI,'run',uncertain)
    report=steps.run_one('example',config())
    assert report['preparation_attempted'] and not report['runtime_attempted']
    assert report['template_cleanup_verified'] is False and report['unresolved_owned_cleanup'] is True
    assert not report['passed'] and not resources
    intent=json.loads((stages[0]/'platform-intent.json').read_text())
    assert intent['registration_attempted'] and not intent.get('template_id')
    assert intent['template_cleanup_verified'] is False


def test_missing_alias_and_successful_delete_cannot_hide_still_present_known_id(prepared,monkeypatch):
    _,_,resources,_=prepared
    monkeypatch.setattr(current,'exact_templates',lambda *args:[])
    original=CLI.run
    def no_op_delete(self,args,*a,**k):
        if args[:2]==['template','delete']:return ''
        return original(self,args,*a,**k)
    monkeypatch.setattr(CLI,'run',no_op_delete)
    cleanup=current.delete_owned_templates
    monkeypatch.setattr(current,'delete_owned_templates',lambda cli,alias,known:cleanup(cli,alias,known,timeout=0))
    async def exercise(*args,**kwargs):args[3].update(application_result='PASS',cleanup_verified=True,commands=[])
    monkeypatch.setattr(current,'exercise',exercise)
    report=steps.run_one('example',config())
    assert report['passed'] is False and report['template_cleanup_verified'] is False
    assert report['unresolved_owned_cleanup'] is True and resources==['owned-template']


def test_prepared_runtime_environment_preserves_original_launch_contract(tmp_path):
    import yaml
    original={'name':'owned','env':{'PRIORITY':'manifest','TOKEN':''},
              'start_cmd':'original start','ready_cmd':'original ready',
              'provides':{'app':{'port':9000}}}
    (tmp_path/'template.yaml').write_text(yaml.safe_dump(original))
    actual=current.prepared_launch_manifest(tmp_path,'owned-template',
        runtime_env={'PATH':'/opt/tool/bin:/usr/bin','PRIORITY':'docker'})
    assert actual['env']=={'PATH':'/opt/tool/bin:/usr/bin','PRIORITY':'manifest','TOKEN':''}
    for key in ['start_cmd','ready_cmd','provides']:assert actual[key]==original[key]
    assert current.prepared_launch_manifest(tmp_path,'owned-template')['env']==original['env']
    assert yaml.safe_load((tmp_path/'template.yaml').read_text())==original
