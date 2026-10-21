"""Reject false managed qualifications while preserving valid unverified entries."""
import json
from pathlib import Path
import pytest,yaml
from check_managed_catalog import check,README_EN,README_ZH
from select_image_templates import catalog_names,select

def fixture(tmp_path):
    doc=tmp_path/'docs/managed/external';doc.mkdir(parents=True)
    for name,headings in [('README.md',README_EN),('README.zh-CN.md',README_ZH)]:
        (doc/name).write_text('# external\n\n'+'\n\n'.join('## '+h+'\n\nScoped content.'for h in headings)+'\n')
    row={'name':'external','provider':'e2b','template_id':'desktop','kind':'provider-managed','documentation':'docs/managed/external/README.md','evidence':'proof.json','verification_scope':'catalog-only-unverified','native_interpreter_verified':False}
    proof={'template':'external','provider':'e2b','template_id':'desktop','passed':False,'status':'NOT_VERIFIED','native_interpreter_verified':False}
    return row,proof

def write(root,row,proof):
    (root/'awesome-templates.yaml').write_text(yaml.safe_dump({'templates':[{'name':'source','path':'source'}],'managed_templates':[row]}))
    (root/'proof.json').write_text(json.dumps(proof))

def test_unverified_metadata_is_valid_but_never_an_installable_source(tmp_path):
    row,proof=fixture(tmp_path);write(tmp_path,row,proof);assert check(tmp_path)==[]
    names=catalog_names(tmp_path);assert names==['source']and select(names,['docs/managed/external/README.md'])==[]
    with pytest.raises(ValueError):select(names,[],requested='external')

@pytest.mark.parametrize('change',['cleanup','claims','provider','identity','fields','docs','missing-status'])
def test_false_qualification_or_incomplete_contract_is_rejected(tmp_path,change):
    row,proof=fixture(tmp_path)
    if change=='cleanup':proof.update(passed=True,checks=['actual SDK']);row['verification_scope']='shell-files'
    elif change=='claims':row['native_interpreter_verified']=True
    elif change=='provider':row['provider']='unknown'
    elif change=='identity':proof['template']='another'
    elif change=='fields':row['path']='external'
    elif change=='docs':(tmp_path/'docs/managed/external/README.zh-CN.md').unlink()
    elif change=='missing-status':proof.pop('status')
    write(tmp_path,row,proof);assert check(tmp_path)

def test_matching_observed_runtime_and_cleanup_can_qualify_only_its_scope(tmp_path):
    row,proof=fixture(tmp_path);row['verification_scope']='shell-files-code-fallback';proof.update(passed=True,cleanup_verified=True,checks=['actual SDK shell/files']);write(tmp_path,row,proof);assert check(tmp_path)==[]


@pytest.mark.parametrize('value',[None,[],False,'invalid'])
def test_invalid_top_level_is_a_validation_failure(tmp_path,value):
    (tmp_path/'awesome-templates.yaml').write_text(yaml.safe_dump(value));assert check(tmp_path)

def test_untyped_provider_and_checks_cannot_bypass_validation(tmp_path):
    row,proof=fixture(tmp_path);row['provider']={};write(tmp_path,row,proof);assert check(tmp_path)
    row['provider']='e2b';row['verification_scope']='runtime';proof.update(passed=True,cleanup_verified=True,checks='not an actual check list');write(tmp_path,row,proof);assert check(tmp_path)
