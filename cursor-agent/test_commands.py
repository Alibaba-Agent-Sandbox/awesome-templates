"""Authored fixed workers only; original native/model code never runs here."""
import importlib.util,json,os,subprocess,sys,threading,time
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('cursor_native_unit',Path(__file__).with_name('runtime.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

@pytest.mark.parametrize('prompt',['',' ',None,0,'a\0b','x'*32769])
def test_bad_prompt_stops_before_configuration_or_native(prompt):
    with pytest.raises(ValueError):r.run(prompt,allow_unsafe_tools=True)

@pytest.mark.parametrize('timeout',[0,601,True,False,'2',None,1.5])
def test_timeout_is_bounded_integer_not_boolean(timeout):
    with pytest.raises(ValueError):r.run('task',command_timeout=timeout,allow_unsafe_tools=True)

@pytest.mark.parametrize('permission',[False,None,0,1,'true',{},[]])
def test_tool_permission_is_explicit_boolean_before_native(permission):
    with pytest.raises(ValueError,match='allow_unsafe_tools=True'):r.run('task',allow_unsafe_tools=permission)

@pytest.mark.parametrize('model',['--bad','space model','x'*201,None])
def test_model_cannot_inject_flags(model):
    with pytest.raises(ValueError,match='model'):r.run('task',model=model,allow_unsafe_tools=True)

def test_workspace_escape_symlink_and_missing_key(tmp_path,monkeypatch):
    monkeypatch.setattr(r,'ROOT',tmp_path);monkeypatch.setattr(r,'KEY','')
    assert r.workspace('')==tmp_path
    with pytest.raises(ValueError):r.workspace('../')
    (tmp_path/'escape').symlink_to('/tmp')
    with pytest.raises(ValueError):r.workspace('escape')
    with pytest.raises(RuntimeError,match='CURSOR_API_KEY is required'):r.run('task',allow_unsafe_tools=True)

def test_presence_check_never_exposes_key_or_claims_authentication(tmp_path,monkeypatch):
    monkeypatch.setattr(r,'KEY','fixed-native-key');monkeypatch.setattr(r,'PREFIX',tmp_path/'absent')
    value=r.setup();assert value['api_key_set']and value['requires_unsafe_optin']
    assert value['vendor_authentication_verified']is False and value['compatible_model_fallback']is False
    assert 'fixed-native-key'not in json.dumps(value)

def test_minimal_child_environment_omits_operator_keys(tmp_path,monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','never-inherit');monkeypatch.setenv('ABX_SERVER_TOKEN','never-inherit')
    env=r.environment(tmp_path,'fixed-native-key')
    assert env['CURSOR_API_KEY']=='fixed-native-key'and env['AGENT_CLI_CREDENTIAL_STORE']=='memory'
    assert not any(x in env for x in ['OPENAI_API_KEY','ABX_SERVER_TOKEN','ALICLOUD_ACCESS_KEY_SECRET','GH_TOKEN','NODE_OPTIONS'])

@pytest.fixture
def worker(tmp_path,monkeypatch):
    project=tmp_path/'project';project.mkdir();binary=tmp_path/'fixed-worker'
    binary.write_text('#!'+sys.executable+'\n'+'''import json,os,pathlib,sys,time
root=pathlib.Path.cwd()
if sys.argv[-1]=='wait':time.sleep(30)
if sys.argv[-1]=='overflow':print('x'*300000,flush=True);raise SystemExit(0)
if sys.argv[-1]=='invalid':print('not-json');raise SystemExit(0)
if sys.argv[-1]=='auth':print('The provided API key is invalid.',file=sys.stderr);raise SystemExit(1)
(root/'observed.json').write_text(json.dumps({'argv':sys.argv[1:],'home':os.environ['HOME'],'operator_key':bool(os.environ.get('OPENAI_API_KEY')),'server_token':bool(os.environ.get('ABX_SERVER_TOKEN'))}))
print(json.dumps({'type':'result','subtype':'success','is_error':False,'result':'FIXED_NATIVE_FINAL'}))
''');binary.chmod(0o755)
    monkeypatch.setattr(r,'ROOT',project);monkeypatch.setattr(r,'KEY','fixed-native-key');monkeypatch.setattr(r,'executable',lambda:str(binary))
    return project

def test_actual_authored_process_literal_argv_fixed_profile_and_private_cleanup(worker,monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','never-inherit');monkeypatch.setenv('ABX_SERVER_TOKEN','never-inherit')
    prompt='literal $(touch should-not-exist); `false`'
    result=r.run(prompt,allow_unsafe_tools=True,model='owned-model');value=json.loads((worker/'observed.json').read_text())
    assert result['stdout']=='FIXED_NATIVE_FINAL'and result['native_completed']and result['permission_profile']=='explicit-owned-sandbox-bypass'
    assert value['argv'][-1]==prompt and '--force'in value['argv']and '--disable-project-configs'in value['argv']and '--disable-auto-update'in value['argv']
    assert value['argv'][value['argv'].index('--sandbox')+1]=='disabled'
    assert not value['operator_key']and not value['server_token']and not Path(value['home']).exists()and not(worker/'should-not-exist').exists()

@pytest.mark.parametrize('prompt,fragment',[('overflow','exceeded'),('invalid','not JSON'),('auth','category=authentication_refused')])
def test_original_failure_and_invalid_completion_never_become_success(worker,prompt,fragment):
    with pytest.raises(RuntimeError,match=fragment):r.run(prompt,allow_unsafe_tools=True)

def test_owned_timeout_preserves_unrelated_process(worker):
    outsider=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'])
    try:
        with pytest.raises(RuntimeError,match='timeout'):r.run('wait',command_timeout=1,allow_unsafe_tools=True)
        assert outsider.poll()is None
    finally:outsider.terminate();outsider.wait(timeout=5)
