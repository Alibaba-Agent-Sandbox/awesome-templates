"""Image selection must preserve runtime coverage and avoid evidence-only rebuilds."""
import importlib.util
from pathlib import Path
import pytest

SPEC = importlib.util.spec_from_file_location('select_image_templates', Path(__file__).with_name('select_image_templates.py'))
selector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(selector)


@pytest.mark.parametrize('changed', [
    ['.agents/evidence/verify/result.md', 'docs/verification.md'],
    ['pi/README.md', 'pi/README.zh-CN.md', 'pi/evidence/result.json'],
    ['README.md', 'awesome-templates.yaml'],
])
def test_prose_evidence_and_catalog_metadata_do_not_build(changed):
    assert selector.select(['pi','python-hello'],changed) == []


@pytest.mark.parametrize('runtime', ['Dockerfile','commands.py','template.yaml','e2e_test.py','server-policy.json','worker.py','package-lock.json','assets/agent.js','test_commands.py','tests/test_runtime.py'])
def test_every_template_runtime_input_selects_its_own_image(runtime):
    assert selector.select(['pi','python-hello'],['pi/'+runtime]) == ['pi']


def test_shared_image_pipeline_inputs_select_all_catalog_images():
    names=selector.catalog_names()
    assert 'pi' in names
    for shared in selector.SHARED_INPUTS:
        assert selector.select(names,[shared]) == names


def test_dispatch_selects_only_requested_deduplicated_catalog_entries():
    assert selector.select(['pi','python-hello'],[], ' pi,python-hello,pi ') == ['pi','python-hello']


@pytest.mark.parametrize('requested',['','pi,','../pi','pi;false','unknown','pi,$(secret)'])
def test_dispatch_rejects_unknown_paths_shell_and_empty_entries(requested):
    with pytest.raises(ValueError,match='catalog names'):
        selector.select(['pi','python-hello'],[],requested)


def test_real_git_prose_followup_cannot_hide_prior_runtime_failure(monkeypatch,tmp_path,capsys):
    import subprocess
    import sys
    import yaml
    def git(*args):
        return subprocess.check_output(['git',*args],cwd=tmp_path,text=True).strip()
    git('init','-q');git('config','user.name','Fixture');git('config','user.email','fixture@example.invalid')
    (tmp_path/'awesome-templates.yaml').write_text(yaml.safe_dump({'templates':[{'path':'pi'},{'path':'python-hello'}]}))
    (tmp_path/'pi').mkdir();(tmp_path/'pi/commands.py').write_text('original')
    git('add','.');git('commit','-qm','initial');base=git('rev-parse','HEAD')
    (tmp_path/'pi/commands.py').write_text('changed runtime');git('add','.');git('commit','-qm','runtime');runtime=git('rev-parse','HEAD')
    evidence=tmp_path/'.agents/evidence/verify/result.md';evidence.parent.mkdir(parents=True);evidence.write_text('verified')
    git('add','.');git('commit','-qm','evidence')
    monkeypatch.setattr(selector,'ROOT',tmp_path)
    monkeypatch.setattr(selector,'catalog_names',lambda: ['pi','python-hello'])
    monkeypatch.setattr(sys,'argv',['select','--event','pull_request','--base',base,'--head','HEAD'])
    assert selector.main()==0 and capsys.readouterr().out.strip()=='["pi"]'


def test_main_push_never_assumes_an_unverified_prior_image_pass(monkeypatch,capsys):
    import sys
    monkeypatch.setattr(selector,'catalog_names',lambda:['pi','python-hello'])
    monkeypatch.setattr(sys,'argv',['select','--event','push','--base','deadbeef','--head','HEAD'])
    assert selector.main()==0 and capsys.readouterr().out.strip()=='["pi","python-hello"]'


def test_automatic_archive_scope_has_an_explicit_task_override():
    import re
    import yaml
    workflow=yaml.safe_load((Path(__file__).resolve().parents[1]/'.github/workflows/image-build.yml').read_text())
    steps=workflow['jobs']['image-build']['steps']
    exports=[step for step in steps if step.get('name') in {'Export selected images for a separate local registry transfer','Retain selected transferable images for one day'}]
    assert len(exports)==2 and exports[0]['if']==exports[1]['if']
    condition=exports[0]['if']
    assert set(re.findall(r"matrix\.template == '([^']+)'",condition))=={'pi','python-hello'}
    assert "success()" in condition and 'inputs.export_images' in condition
    assert "needs.plan.outputs.export_all_selected == 'true'" in condition
    assert exports[1]['with']['retention-days']==1


def test_task_export_policy_does_not_change_image_selection(tmp_path):
    import json
    assert selector.export_all_selected(tmp_path) is False
    folder=tmp_path/'.github';folder.mkdir()
    file=folder/'image-export-policy.json'
    file.write_text(json.dumps({'automatic':'all-selected','reason':'explicit acceptance task'}))
    assert selector.export_all_selected(tmp_path) is True
    assert selector.select(['pi','python-hello'],['.github/image-export-policy.json'])==[]
    file.write_text(json.dumps({'automatic':'default'}))
    assert selector.export_all_selected(tmp_path) is False


@pytest.mark.parametrize('value',[{}, {'automatic':'unknown'}, {'automatic':'all-selected'}, []])
def test_task_export_policy_rejects_ambiguous_or_unreasoned_modes(tmp_path,value):
    import json
    (tmp_path/'.github').mkdir()
    (tmp_path/'.github/image-export-policy.json').write_text(json.dumps(value))
    with pytest.raises(ValueError):selector.export_all_selected(tmp_path)
