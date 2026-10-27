"""Authored native-process substitutes exercise boundaries; these are not L3."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).parent
spec=importlib.util.spec_from_file_location('tested_copilot_commands',ROOT/'commands.py')
commands=importlib.util.module_from_spec(spec);spec.loader.exec_module(commands)

@pytest.fixture
def configured(tmp_path,monkeypatch):
    workspace=tmp_path/'workspace';workspace.mkdir()
    monkeypatch.setattr(commands,'_ROOT',workspace)
    monkeypatch.setattr(commands,'_CONFIG',{'COPILOT_PROVIDER_BASE_URL':'https://provider.invalid/v1','COPILOT_PROVIDER_API_KEY':'fake-native-test-key-123','COPILOT_MODEL':'test-model'})
    return workspace

@pytest.mark.parametrize('kwargs',[
 {'prompt':''},{'prompt':'\x00'},{'prompt':'界'*11000},{'prompt':'task','allow_write':'true'},
 {'prompt':'task','command_timeout':True},{'prompt':'task','command_timeout':601},
 {'prompt':'task','cwd':'..'},{'prompt':'task','cwd':'/nonexistent'},
])
def test_rejects_invalid_inputs_before_process(configured,monkeypatch,kwargs):
    monkeypatch.setattr(commands,'_run',lambda *a,**k:pytest.fail('invalid input reached native process'))
    with pytest.raises(ValueError):commands.copilot(**kwargs)


def test_resolved_symlink_cannot_escape_workspace(configured,tmp_path,monkeypatch):
    (configured/'escape').symlink_to(tmp_path,target_is_directory=True)
    monkeypatch.setattr(commands,'_run',lambda *a,**k:pytest.fail('escaped cwd reached native process'))
    with pytest.raises(ValueError):commands.copilot('task',cwd='escape')

@pytest.mark.parametrize('write',[False,True])
def test_native_argv_uses_fixed_tools_and_literal_prompt(configured,monkeypatch,write):
    calls=[]
    monkeypatch.setattr(commands,'_run',lambda args,**kw:calls.append((args,kw)) or {'exit_code':0})
    prompt='--share-gist; $(touch escaped)'
    commands.copilot(prompt,allow_write=write)
    argv,kw=calls[0]
    assert argv[-1]=='--prompt='+prompt
    tools=argv[argv.index('--available-tools')+1:-1]
    assert set(tools)==({'view','glob','grep','edit','create','apply_patch'} if write else {'view','glob','grep'})
    assert '--allow-all-paths' not in argv and '--allow-all-urls' not in argv
    assert '--disable-builtin-mcps' in argv and '--no-custom-instructions' in argv
    assert kw['cwd']==configured and kw['model'] is True


def test_only_explicit_byok_credentials_enter_private_process(configured,monkeypatch,tmp_path):
    monkeypatch.setenv('GITHUB_TOKEN','unrelated-github-test')
    monkeypatch.setenv('COPILOT_PROVIDER_API_KEY_COMMAND','unsafe command')
    monkeypatch.setenv('COPILOT_PROVIDER_HEADERS','secret:unrelated')
    monkeypatch.setenv('OPENAI_API_KEY','unrelated-model-test')
    env=commands._env(tmp_path,model=True)
    for key in ['GITHUB_TOKEN','COPILOT_PROVIDER_API_KEY_COMMAND','COPILOT_PROVIDER_HEADERS','OPENAI_API_KEY']:assert key not in env
    assert env['HOME']==str(tmp_path) and env['COPILOT_OFFLINE']=='true'
    assert env['COPILOT_PROVIDER_WIRE_API']=='completions'
    readonly=commands._env(tmp_path,model=False)
    assert not any(k in readonly for k in commands._CONFIG)

@pytest.mark.parametrize('field,value',[
 ('COPILOT_PROVIDER_BASE_URL','http://remote.invalid/v1'),
 ('COPILOT_PROVIDER_BASE_URL','https://user:pass@remote.invalid/v1'),
 ('COPILOT_PROVIDER_BASE_URL','https://remote.invalid/v1?secret=token'),
 ('COPILOT_PROVIDER_BASE_URL','https://remote.invalid:bad/v1'),
 ('COPILOT_PROVIDER_API_KEY',''),('COPILOT_PROVIDER_API_KEY','line\nbreak'),
 ('COPILOT_MODEL','--model=bad'),
])
def test_bad_configuration_fails_without_network(configured,monkeypatch,tmp_path,field,value):
    commands._CONFIG[field]=value
    with pytest.raises(ValueError):commands._env(tmp_path,model=True)


def test_nonzero_status_redaction_private_cleanup_with_authored_process(configured,tmp_path,monkeypatch):
    # This is a fixed test process authored here, never model-generated source.
    binary=tmp_path/'copilot';capture=tmp_path/'capture.json'
    binary.write_text('#!'+sys.executable+'\nimport json,os,pathlib,sys\n'
        +f'pathlib.Path({str(capture)!r}).write_text(json.dumps({{"home":os.environ["HOME"],"argv":sys.argv[1:]}}))\n'
        +'print(os.environ["COPILOT_PROVIDER_API_KEY"])\n'
        +'print(json.dumps(os.environ["COPILOT_PROVIDER_API_KEY"]),file=sys.stderr)\n'
        +'raise SystemExit(23)\n')
    binary.chmod(0o700);monkeypatch.setattr(commands.shutil,'which',lambda value:str(binary))
    result=commands.copilot('fixed harmless test')
    assert result['exit_code']==23
    assert 'fake-native-test-key' not in result['stdout']+result['stderr']
    assert '[REDACTED]' in result['stdout']
    assert not Path(json.loads(capture.read_text())['home']).exists()


def test_timeout_cleans_detached_authored_child_and_preserves_unrelated_process(configured,tmp_path,monkeypatch):
    import subprocess
    unrelated=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'])
    binary=tmp_path/'copilot';pidfile=tmp_path/'owned-child.pid'
    binary.write_text('#!'+sys.executable+'\nimport subprocess,sys,time,pathlib\n'
       +'child=subprocess.Popen([sys.executable,"-c","import time;time.sleep(30)"],start_new_session=True)\n'
       +f'pathlib.Path({str(pidfile)!r}).write_text(str(child.pid))\n'
       +'time.sleep(30)\n')
    binary.chmod(0o700);monkeypatch.setattr(commands.shutil,'which',lambda value:str(binary))
    try:
        with pytest.raises(RuntimeError,match='timeout'):commands.copilot('authored timeout case',command_timeout=1)
        assert unrelated.poll() is None
        assert pidfile.exists()
        pid=int(pidfile.read_text());stat=Path('/proc')/str(pid)/'stat'
        assert not stat.exists() or stat.read_text().split(') ',1)[1].split()[0]=='Z'
    finally:
        unrelated.terminate();unrelated.wait(timeout=5)
