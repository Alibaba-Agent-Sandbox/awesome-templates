"""Authored fixed workers test contracts; original Devin runs only on owned cloud."""
import importlib.util,json,os,subprocess,sys
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('devin_native_unit',Path(__file__).with_name('runtime.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

@pytest.mark.parametrize('prompt',['',' ',None,0,'a\0b','x'*32769])
def test_bad_prompt_stops_before_native(prompt):
    with pytest.raises(ValueError):r.run(prompt,allow_unsafe_tools=True)

@pytest.mark.parametrize('timeout',[0,601,True,False,'2',None,1.5])
def test_timeout_is_bounded_integer(timeout):
    with pytest.raises(ValueError):r.run('task',command_timeout=timeout,allow_unsafe_tools=True)

@pytest.mark.parametrize('permission',[False,None,0,1,'true',{},[]])
def test_permission_is_explicit_boolean(permission):
    with pytest.raises(ValueError,match='allow_unsafe_tools=True'):r.run('task',allow_unsafe_tools=permission)

@pytest.mark.parametrize('model',['--bad','space model','x'*201,None])
def test_model_cannot_inject_flags(model):
    with pytest.raises(ValueError,match='model'):r.run('task',model=model,allow_unsafe_tools=True)

def test_workspace_escape_symlink_and_project_configuration_preserved(tmp_path,monkeypatch):
    project=tmp_path/'workspace';project.mkdir();monkeypatch.setattr(r,'ROOT',project)
    with pytest.raises(ValueError):r.workspace('../')
    (project/'escape').symlink_to('/tmp')
    with pytest.raises(ValueError):r.workspace('escape')
    config=project/'.devin';config.mkdir();(config/'config.json').write_text('{"auto_update":true}')
    with pytest.raises(ValueError,match='project .devin'):r.run('task',allow_unsafe_tools=True)
    assert(config/'config.json').read_text()=='{"auto_update":true}'

def test_readonly_presence_does_not_read_or_disclose_credentials(tmp_path,monkeypatch):
    monkeypatch.setattr(r,'CREDENTIALS_FILE','/private/absent-auth-file')
    state=r.setup();assert state['credentials_file_set']and state['requires_unsafe_optin']
    assert not state['vendor_authentication_verified']and not state['compatible_model_fallback']
    assert '/private/absent-auth-file'not in json.dumps(state)

def test_minimal_environment_and_private_config(tmp_path,monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','never-inherit');monkeypatch.setenv('DEVIN_API_KEY','never-inherit')
    env=r.environment(tmp_path);assert not any(key in env for key in ['DEVIN_API_KEY','OPENAI_API_KEY','ABX_SERVER_TOKEN','GH_TOKEN','ALICLOUD_ACCESS_KEY_SECRET','DEVIN_CREDENTIALS_FILE'])
    config=Path(r.configuration(tmp_path));x=json.loads(config.read_text())
    assert x['auto_update']is False and x['subagents_enabled']is False and not any(x['read_config_from'].values())
    assert config.stat().st_mode&0o777==0o600

@pytest.mark.parametrize('kind',['symlink','public','invalid','large','fifo','inside-workspace'])
def test_credentials_reject_unprivate_or_invalid_input(tmp_path,monkeypatch,kind):
    project=tmp_path/'workspace';project.mkdir();monkeypatch.setattr(r,'ROOT',project)
    file=tmp_path/'credentials.toml';file.write_text('token="fixed-authored-secret"');file.chmod(0o600)
    if kind=='symlink':link=tmp_path/'link';link.symlink_to(file);file=link
    elif kind=='public':file.chmod(0o644)
    elif kind=='invalid':file.write_text('not valid TOML')
    elif kind=='large':file.write_bytes(b'x'*65537)
    elif kind=='fifo':file.unlink();os.mkfifo(file,0o600)
    elif kind=='inside-workspace':file=project/'credentials.toml';file.write_text('token="fixed-authored-secret"');file.chmod(0o600)
    monkeypatch.setattr(r,'CREDENTIALS_FILE',str(file))
    with pytest.raises(ValueError):r.credentials()

@pytest.fixture
def worker(tmp_path,monkeypatch):
    project=tmp_path/'workspace';project.mkdir();binary=tmp_path/'fixed-worker'
    binary.write_text('#!'+sys.executable+'\n'+'''import json,os,pathlib,sys,time
root=pathlib.Path.cwd();prompt=sys.argv[-1]
if prompt=='wait':time.sleep(30)
if prompt=='overflow':print('x'*300000,flush=True);raise SystemExit(0)
if prompt=='empty':raise SystemExit(0)
if prompt=='auth':print('Please log in using devin auth login',file=sys.stderr);raise SystemExit(1)
home=pathlib.Path(os.environ['HOME']);credential=home/'data/devin/credentials.toml'
(root/'observed.json').write_text(json.dumps({'argv':sys.argv[1:],'home':str(home),'config':json.loads(pathlib.Path(sys.argv[sys.argv.index('--config')+1]).read_text()),'credentials':credential.read_text()if credential.exists()else '', 'credential_mode':credential.stat().st_mode&0o777 if credential.exists()else None,'operator_key':bool(os.environ.get('OPENAI_API_KEY'))}))
print('FIXED_NATIVE_FINAL fixed-authored-secret'if prompt=='leak'else'FIXED_NATIVE_FINAL')
''');binary.chmod(0o755)
    monkeypatch.setattr(r,'ROOT',project);monkeypatch.setattr(r,'CREDENTIALS_FILE','');monkeypatch.setattr(r,'executable',lambda:str(binary));return project

def test_literal_argv_and_private_state_cleanup(worker,monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','never-inherit');prompt='literal $(touch should-not-exist); `false`'
    result=r.run(prompt,allow_unsafe_tools=True,model='owned-model');x=json.loads((worker/'observed.json').read_text())
    assert result['stdout']=='FIXED_NATIVE_FINAL'and result['native_completed']
    assert x['argv'][-2:]==['--print',prompt]and x['argv'][x['argv'].index('--permission-mode')+1]=='dangerous'
    assert x['argv'][x['argv'].index('--respect-workspace-trust')+1]=='false'
    assert not x['operator_key']and not Path(x['home']).exists()and not(worker/'should-not-exist').exists()

def test_original_credential_bytes_copied_privately_and_preserved(worker,monkeypatch):
    original=worker.parent/'credentials.toml';content='[account]\ntoken="fixed-authored-secret"\n';original.write_text(content);original.chmod(0o600)
    monkeypatch.setattr(r,'CREDENTIALS_FILE',str(original));r.run('fixed',allow_unsafe_tools=True)
    x=json.loads((worker/'observed.json').read_text());assert x['credentials']==content and x['credential_mode']==0o600
    assert original.read_text()==content and not Path(x['home']).exists()

@pytest.mark.parametrize('prompt,fragment',[('overflow','exceeded'),('empty','empty'),('auth','category=authentication_refused')])
def test_native_failure_never_becomes_success(worker,prompt,fragment):
    with pytest.raises(RuntimeError,match=fragment):r.run(prompt,allow_unsafe_tools=True)

def test_timeout_preserves_unrelated_process(worker):
    outsider=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'])
    try:
        with pytest.raises(RuntimeError,match='timeout'):r.run('wait',command_timeout=1,allow_unsafe_tools=True)
        assert outsider.poll()is None
    finally:outsider.terminate();outsider.wait(timeout=5)


def test_original_credential_string_never_leaks_in_returned_native_text(worker,monkeypatch):
    original=worker.parent/'credentials.toml';original.write_text('token="fixed-authored-secret"');original.chmod(0o600)
    monkeypatch.setattr(r,'CREDENTIALS_FILE',str(original));result=r.run('leak',allow_unsafe_tools=True)
    assert 'fixed-authored-secret'not in json.dumps(result)and '[REDACTED]'in result['stdout']
