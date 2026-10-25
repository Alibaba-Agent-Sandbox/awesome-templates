"""Non-executable native metadata controls and generated-code target guard."""
import importlib.util
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('devin_controller_fixture',Path(__file__).with_name('e2e_test.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
def result():return {'exit_code':0,'native_completed':True,'native_version':'3000.11.92','archive_sha256':'2d829139682e038cf122510f1170eee3d7060bcc7ebf92445cbc5d28c9fbcfa0','permission_profile':'explicit-owned-sandbox-bypass','stdout':'FIXED'}
def test_valid_native_metadata():assert c.final_text(result())=='FIXED'
@pytest.mark.parametrize('key,value',[('exit_code',True),('exit_code',1),('native_completed',False),('native_version','other'),('archive_sha256','0'*64),('permission_profile','implicit'),('stdout',None)])
def test_marker_cannot_replace_original_native_completion(key,value):
    data=result();data[key]=value;assert c.final_text(data)==''
def test_model_requires_remote_host_and_native_auth_requires_explicit_opt_in(monkeypatch):
    monkeypatch.setenv('E2E_RUN_LLM','1');monkeypatch.setenv('E2E_REMOTE_SANDBOX','1');c.RESULTS.clear()
    c.model_check(object(),'/tmp/not-created','http://127.0.0.1:9000')
    monkeypatch.delenv('E2E_REMOTE_SANDBOX')
    c.native_auth_check(object(),'/tmp/not-created','http://127.0.0.1:9000')
    assert c.RESULTS==[False,False]
