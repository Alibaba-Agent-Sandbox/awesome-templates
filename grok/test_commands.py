"""Authored local boundary/process tests; no real model or generated source."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import pytest

s=importlib.util.spec_from_file_location('grok_owned_command_tests',Path(__file__).with_name('commands.py'))
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
    with pytest.raises(ValueError):c.grok(**args)


def test_resolved_symlink_cannot_escape_workspace(configured,tmp_path,monkeypatch):
    (configured/'escape').symlink_to(tmp_path,target_is_directory=True)
    monkeypatch.setattr(c,'_run',lambda *a,**k:pytest.fail('escaped directory reached CLI'))
    with pytest.raises(ValueError):c.grok('x',cwd='escape')


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
    monkeypatch.setenv('GROK_BIN_PATH','unrelated-runtime-override')
    private=tmp_path/'private';private.mkdir(mode=0o700)
    env=c._environment(private,model=True);c._profile(private,model=True)
    assert env['ABX_GROK_MODEL_KEY']==c._CONFIG['MODEL_API_KEY']
    assert not any(key in env for key in ['GITHUB_TOKEN','ALICLOUD_ACCESS_KEY_SECRET','GROK_BIN_PATH','GROK_API_KEY'])
    import tomllib
    path=private/'.grok/config.toml';settings=tomllib.loads(path.read_text())['model']['abx-approved']
    assert settings['base_url']==c._CONFIG['MODEL_BASE_URL'] and settings['api_backend']=='chat_completions'
    assert settings['env_key']=='ABX_GROK_MODEL_KEY' and 'api_key'not in settings
    assert path.stat().st_mode&0o777==0o600 and c._CONFIG['MODEL_API_KEY']not in path.read_text()
    assert 'ABX_GROK_MODEL_KEY'not in c._environment(private,model=False)


def test_actual_authored_process_literal_stdin_redaction_nonzero_and_private_cleanup(configured,tmp_path,monkeypatch):
    capture=tmp_path/'capture.json';binary=tmp_path/'authored-grok'
    binary.write_text('#!'+sys.executable+'\nimport json,os,pathlib,sys,tomllib\n'
        +f'pathlib.Path({str(capture)!r}).write_text(json.dumps({{"home":os.environ["HOME"],"argv":sys.argv[1:],"stdin":sys.stdin.read(),"config":tomllib.loads((pathlib.Path(os.environ["GROK_HOME"])/"config.toml").read_text())}}))\n'
        +'print(os.environ["ABX_GROK_MODEL_KEY"])\nraise SystemExit(23)\n')
    binary.chmod(0o700);monkeypatch.setattr(c,'_paths',lambda:str(binary));prompt='--update; $(touch escaped)'
    result=c.grok(prompt);state=json.loads(capture.read_text())
    assert state['stdin']==prompt and prompt not in state['argv']
    assert state['argv'][state['argv'].index('--prompt-file')+1]=='/dev/stdin'
    assert 'write_file'not in state['argv'][state['argv'].index('--tools')+1].split(',')
    assert '--no-subagents'in state['argv'] and state['argv'][state['argv'].index('--model')+1]=='abx-approved'
    assert not Path(state['home']).exists() and result['exit_code']==23
    assert 'synthetic-only-key'not in result['stdout']+result['stderr'] and '[REDACTED]'in result['stdout']
    assert 'api_key'not in state['config']['model']['abx-approved'] and not(configured/'escaped').exists()


def test_busy_version_cannot_replace_active_lifecycle():
    c._LOCK.acquire()
    try:
        with pytest.raises(RuntimeError,match='active'):c.grok_version()
    finally:c._LOCK.release()
