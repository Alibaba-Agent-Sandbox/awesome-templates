"""Authored local boundary/process tests; no real model or generated source."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import pytest

s=importlib.util.spec_from_file_location('cline_owned_command_tests',Path(__file__).with_name('commands.py'))
c=importlib.util.module_from_spec(s)
s.loader.exec_module(c)


@pytest.fixture
def configured(tmp_path,monkeypatch):
    root=tmp_path/'project';root.mkdir()
    monkeypatch.setattr(c,'_ROOT',root)
    monkeypatch.setattr(c,'_CONFIG',{'MODEL_API_KEY':'synthetic-only-key-123','MODEL_BASE_URL':'https://provider.example.invalid/v1','MODEL':'fixture-model'})
    return root


@pytest.mark.parametrize('args',[
    {'prompt':''},{'prompt':'\0'},{'prompt':'界'*11000},{'prompt':'x','command_timeout':True},
    {'prompt':'x','command_timeout':601},{'prompt':'x','cwd':'..'},{'prompt':'x','cwd':'/outside-workspace'},
])
def test_invalid_input_stops_before_native_process(configured,monkeypatch,args):
    monkeypatch.setattr(c,'_run',lambda *a,**k:pytest.fail('invalid input reached CLI'))
    with pytest.raises(ValueError):c.cline(**args)


def test_resolved_symlink_cannot_escape_workspace(configured,tmp_path,monkeypatch):
    (configured/'escape').symlink_to(tmp_path,target_is_directory=True)
    monkeypatch.setattr(c,'_run',lambda *a,**k:pytest.fail('escaped directory reached CLI'))
    with pytest.raises(ValueError):c.cline('x',cwd='escape')


@pytest.mark.parametrize('field,value',[
    ('MODEL_API_KEY',''),('MODEL_API_KEY','line\nbreak'),('MODEL_BASE_URL','http://remote.invalid/v1'),
    ('MODEL_BASE_URL','https://user:pass@remote.invalid'),('MODEL_BASE_URL','https://remote.invalid:bad/v1'),
    ('MODEL_BASE_URL','https://remote.invalid/v1?key=value'),('MODEL','--model=bad'),
])
def test_bad_provider_configuration_never_networks(configured,field,value):
    c._CONFIG[field]=value
    with pytest.raises(ValueError):c._validate_config()


def test_profile_contains_no_key_and_host_credentials_are_not_forwarded(configured,tmp_path,monkeypatch):
    monkeypatch.setenv('GITHUB_TOKEN','unrelated-host-token')
    monkeypatch.setenv('ALICLOUD_ACCESS_KEY_SECRET','unrelated-cloud-secret')
    monkeypatch.setenv('CLINE_BIN_PATH','unrelated-runtime-override')
    private=tmp_path/'private';private.mkdir(mode=0o700)
    env=c._environment(private,model=True);c._profile(private,model=True)
    assert env['OPENAI_API_KEY']==c._CONFIG['MODEL_API_KEY']
    assert not any(key in env for key in ['GITHUB_TOKEN','ALICLOUD_ACCESS_KEY_SECRET','CLINE_BIN_PATH','CLINE_API_KEY'])
    settings=json.loads((private/'data/settings/providers.json').read_text())['providers']['openai-compatible']['settings']
    assert settings['baseUrl']==c._CONFIG['MODEL_BASE_URL'] and settings['protocol']=='openai-chat'
    assert Path(env['CLINE_PROVIDER_SETTINGS_PATH'])==private/'data/settings/providers.json'
    assert 'apiKey'not in settings
    for path in private.rglob("*.json"):
        assert path.stat().st_mode&0o777==0o600
        assert c._CONFIG['MODEL_API_KEY'] not in path.read_text()
    assert 'OPENAI_API_KEY'not in c._environment(private,model=False)


def test_actual_authored_process_literal_stdin_redaction_nonzero_and_private_cleanup(configured,tmp_path,monkeypatch):
    capture=tmp_path/'capture.json';binary=tmp_path/'authored-cline'
    binary.write_text('#!'+sys.executable+'\nimport json,os,pathlib,sys\n'
        +f'pathlib.Path({str(capture)!r}).write_text(json.dumps({{"home":os.environ["HOME"],"argv":sys.argv[1:],"stdin":sys.stdin.read(),"providers":json.load(open(os.environ["CLINE_PROVIDER_SETTINGS_PATH"]))}}))\n'
        +'assert "Complete the task provided on standard input." in sys.argv, "upstream JSON preflight requires a positional prompt before reading stdin"\n'
        +'print(os.environ["OPENAI_API_KEY"])\nprint(json.dumps(os.environ["OPENAI_API_KEY"]),file=sys.stderr)\nraise SystemExit(23)\n')
    binary.chmod(0o700);monkeypatch.setattr(c,'_paths',lambda:str(binary))
    prompt='--update; $(touch escaped)'
    result=c.cline(prompt)
    state=json.loads(capture.read_text());assert state['stdin']==prompt and prompt not in state['argv']
    assert '--yolo'in state['argv'] and '--json'in state['argv'] and '--zen'not in state['argv']
    assert state['argv'][state['argv'].index('--provider')+1]=='openai-compatible'
    assert not Path(state['home']).exists() and result['exit_code']==23
    assert 'synthetic-only-key'not in result['stdout']+result['stderr'] and '[REDACTED]'in result['stdout']
    assert 'apiKey'not in state['providers']['providers']['openai-compatible']['settings']
    assert not(configured/'escaped').exists()


def test_busy_version_cannot_replace_active_lifecycle():
    c._LOCK.acquire()
    try:
        with pytest.raises(RuntimeError,match='active'):c.cline_version()
    finally:c._LOCK.release()
