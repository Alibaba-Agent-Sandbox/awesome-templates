"""Argument/ownership/privacy fixtures; never executes the original agent locally."""
import importlib.util,json,os,sys
from pathlib import Path
import pytest
s=importlib.util.spec_from_file_location('claude_byok_fixture',Path(__file__).with_name('byok.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
@pytest.mark.parametrize('prompt',['',' ',None,'x\0','x'*32769])
def test_invalid_prompt_before_configuration_or_process(prompt):
 with pytest.raises(ValueError):b.run(prompt)
@pytest.mark.parametrize('timeout',[True,False,'1',0,601,1.2,None])
def test_invalid_integer_timeout(timeout):
 with pytest.raises(ValueError):b.run('x',command_timeout=timeout)
def test_workspace_escape_and_own_valid_project(tmp_path,monkeypatch):
 monkeypatch.setattr(b,'ROOT',tmp_path);assert b.workspace('')==tmp_path
 with pytest.raises(ValueError):b.workspace('../')
 (tmp_path/'outside').symlink_to('/tmp')
 with pytest.raises(ValueError):b.workspace('outside')
def test_minimal_child_environment_omits_real_keys(tmp_path,monkeypatch):
 monkeypatch.setenv('OPENAI_API_KEY','not-forwarded');monkeypatch.setenv('ABX_SERVER_TOKEN','not-forwarded');env=b.environment(tmp_path)
 assert not any(x in env for x in ['OPENAI_API_KEY','ABX_SERVER_TOKEN','CLAUDE_MODEL_API_KEY','GITHUB_TOKEN'])
 assert env['DISABLE_AUTOUPDATER']=='1'and env['MAX_THINKING_TOKENS']=='0'and env['CLAUDE_CONFIG_DIR']==str(tmp_path/'config')
def test_setup_no_values_or_vendor_claim(monkeypatch):
 monkeypatch.setattr(b,'MODEL',dict(MODEL_API_KEY='root-secret',MODEL_BASE_URL='https://private.test/v1',MODEL='model'))
 assert b.setup()['model_key_set']and b.setup()['vendor_account_verified']is False
 assert 'root-secret'not in json.dumps(b.setup())and'private.test'not in json.dumps(b.setup())
def test_owned_process_descendant_cleanup_and_output_bound(tmp_path):
 # Authored fixed worker, independent unrelated process remains alive.
 import subprocess
 outsider=subprocess.Popen([sys.executable,'-c','import time;time.sleep(20)'])
 try:
  code,out,err=b.PROCESS.run([sys.executable,'-c','import os,time;pid=os.fork();\nif pid==0:time.sleep(20)\nelse:print("DONE",flush=True)'],cwd=tmp_path,env={'PATH':os.environ['PATH']},timeout=3)
  assert code==0 and out.strip()=='DONE'and outsider.poll()is None
  with pytest.raises(RuntimeError,match='output exceeded'):b.PROCESS.run([sys.executable,'-c','print("x"*300000)'],cwd=tmp_path,env={'PATH':os.environ['PATH']},timeout=3)
 finally:outsider.terminate();outsider.wait(timeout=5)
def test_authored_process_timeout(tmp_path):
 with pytest.raises(RuntimeError,match='exceeded timeout'):b.PROCESS.run([sys.executable,'-c','import time;time.sleep(20)'],cwd=tmp_path,env={'PATH':os.environ['PATH']},timeout=.05)


@pytest.mark.parametrize('optin',[False,None,1,'true'])
def test_tool_permission_bypass_requires_explicit_boolean_optin(tmp_path,monkeypatch,optin):
    monkeypatch.setattr(b,'ROOT',tmp_path);monkeypatch.setattr(b,'binary',lambda:pytest.fail('must not start native without explicit opt-in'))
    with pytest.raises(ValueError,match='allow_unsafe_tools'):b.run('fixed request',allow_unsafe_tools=optin)
