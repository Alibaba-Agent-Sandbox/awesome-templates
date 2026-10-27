"""Authored process/configuration boundaries; no real model acceptance."""
import importlib.util,json,sys
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('droid_byok_boundary_tests',Path(__file__).with_name('byok.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)


@pytest.fixture
def configured(tmp_path,monkeypatch):
    root=tmp_path/'project';root.mkdir()
    monkeypatch.setattr(c,'ROOT',root)
    monkeypatch.setattr(c,'CONFIG',{'MODEL_API_KEY':'synthetic-only-key-123','MODEL_BASE_URL':'https://model.example.invalid/v1','MODEL':'fixture-model'})
    return root


@pytest.mark.parametrize('parameters',[
    {'prompt':''},{'prompt':'\0'},{'prompt':'界'*11000},{'prompt':'x','command_timeout':True},
    {'prompt':'x','command_timeout':601},{'prompt':'x','cwd':'..'},{'prompt':'x','cwd':'/outside-workspace'}])
def test_invalid_inputs_never_launch_native(configured,monkeypatch,parameters):
    monkeypatch.setattr(c,'binary',lambda:pytest.fail('invalid request reached native binary'))
    with pytest.raises(ValueError):c.droid_byok(**parameters)


@pytest.mark.parametrize('field,value',[
    ('MODEL_API_KEY',''),('MODEL_API_KEY','line\nbreak'),('MODEL_BASE_URL','http://remote.invalid/v1'),
    ('MODEL_BASE_URL','https://@remote.invalid'),('MODEL_BASE_URL','https://user:pass@remote.invalid'),
    ('MODEL_BASE_URL','https://remote.invalid:bad/v1'),('MODEL_BASE_URL','https://remote.invalid/v1?key=value'),('MODEL','--unsafe')])
def test_invalid_provider_configuration_never_networks(configured,field,value):
    c.CONFIG[field]=value
    with pytest.raises(ValueError):c.validate_config()


def test_native_profile_keeps_key_reference_and_excludes_operator_credentials(configured,tmp_path,monkeypatch):
    for key in ['GITHUB_TOKEN','ALICLOUD_ACCESS_KEY_SECRET','FACTORY_API_KEY','DROID_BIN_PATH','OPENAI_API_KEY']:
        monkeypatch.setenv(key,'unrelated-operator-secret')
    private=tmp_path/'private';private.mkdir(mode=0o700);c.profile(private)
    path=private/'.factory/settings.json';model=json.loads(path.read_text())['customModels'][0]
    assert model['model']==c.CONFIG['MODEL']and model['baseUrl']==c.CONFIG['MODEL_BASE_URL']
    assert model['provider']=='generic-chat-completion-api'and model['apiKey']=='${ABX_DROID_MODEL_KEY}'
    assert c.CONFIG['MODEL_API_KEY']not in path.read_text()and path.stat().st_mode&0o777==0o600
    env=c.environment(private,model=True)
    assert env['ABX_DROID_MODEL_KEY']==c.CONFIG['MODEL_API_KEY']
    assert not any(key in env for key in ['GITHUB_TOKEN','ALICLOUD_ACCESS_KEY_SECRET','FACTORY_API_KEY','DROID_BIN_PATH','OPENAI_API_KEY'])
    assert 'ABX_DROID_MODEL_KEY'not in c.environment(private,model=False)


@pytest.mark.parametrize('exit_code',[0,23])
def test_actual_authored_process_literal_stdin_native_exit_and_private_cleanup(configured,tmp_path,monkeypatch,exit_code):
    capture=tmp_path/'capture.json';binary=tmp_path/'authored-droid'
    binary.write_text('#!'+sys.executable+'\nimport json,os,pathlib,sys\n'+
        f'pathlib.Path({str(capture)!r}).write_text(json.dumps({{"home":os.environ["HOME"],"stdin":sys.stdin.read(),"argv":sys.argv[1:],"settings":json.loads((pathlib.Path(os.environ["HOME"])/".factory/settings.json").read_text())}}))\n'+
        'print(os.environ["ABX_DROID_MODEL_KEY"])\n'+f'raise SystemExit({exit_code})\n')
    binary.chmod(0o700);monkeypatch.setattr(c,'binary',lambda:str(binary));prompt='--update; $(touch escaped)'
    result=c.droid_byok(prompt);state=json.loads(capture.read_text())
    assert state['stdin'].endswith('\n\n'+prompt)and json.dumps(str(configured))in state['stdin']and prompt not in state['argv']
    assert state['argv'][state['argv'].index('--model')+1]=='custom:fixture-model'
    assert state['argv'][state['argv'].index('--auto')+1]=='low'
    assert '--disable-builtin-skills'in state['argv']
    assert state['argv'][state['argv'].index('--settings')+1]==str(Path(state['home'])/'.factory/settings.json')
    assert state['argv'][state['argv'].index('--cwd')+1]==state['home']
    assert state['argv'][state['argv'].index('--only-tools')+1]=='Read,Edit,Create,Grep,Glob,LS'
    assert state['settings']['customModels'][0]['apiKey']=='${ABX_DROID_MODEL_KEY}'
    assert result['exit_code']==exit_code and not Path(state['home']).exists()
    assert c.CONFIG['MODEL_API_KEY']not in result['stdout']+result['stderr']and'[REDACTED]'in result['stdout']
    assert not(configured/'escaped').exists()


def test_busy_call_cannot_replace_active_owner(configured):
    c.LOCK.acquire()
    try:
        with pytest.raises(RuntimeError,match='active'):c.droid_byok('fixed authored task')
    finally:c.LOCK.release()


def test_new_process_output_bound_stops_unbounded_legacy_output(tmp_path):
    with pytest.raises(RuntimeError,match='output exceeded'):
        c.process.run([sys.executable,'-c','import sys;sys.stdout.write("x"*400000)'],cwd=tmp_path,timeout=5,env={'PATH':'/usr/local/bin:/usr/bin:/bin'})
