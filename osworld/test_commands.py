"""Real process ownership regressions; fixture workers are not desktop evidence."""
import importlib.util
import os
from pathlib import Path
import signal
import subprocess
import sys

import pytest

spec = importlib.util.spec_from_file_location('osworld_test_commands', Path(__file__).with_name('commands.py'))
commands = importlib.util.module_from_spec(spec)
spec.loader.exec_module(commands)


@pytest.fixture(autouse=True)
def cleanup():
    yield
    commands.desktop_stop()


def worker(monkeypatch, tmp_path, body):
    monkeypatch.setenv('WORKSPACE', str(tmp_path))
    monkeypatch.setenv('OSWORLD_RUNTIME_PYTHON', sys.executable)
    monkeypatch.setattr(commands.shutil, 'which', lambda name: '/fixture/'+name)
    script = tmp_path / 'fixture.py'
    script.write_text('import json,sys,os,time,subprocess,signal\nfrom pathlib import Path\n'+body)
    original = subprocess.Popen
    def launch(argv, **kwargs):
        assert len(argv) == 3 and argv[1].endswith('runtime.py')
        return original([argv[0], str(script), argv[2]], **kwargs)
    monkeypatch.setattr(commands.subprocess, 'Popen', launch)


def live(pid):
    try:
        return Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[0] != 'Z'
    except FileNotFoundError:
        return False


def test_real_worker_preserves_home_but_isolates_profile_without_secrets_or_prompt_argv(monkeypatch, tmp_path):
    monkeypatch.setenv('OPENAI_API_KEY', 'fixture-private-key')
    monkeypatch.setenv('ABX_SERVER_TOKEN', 'fixture-server-token')
    monkeypatch.setenv('DISPLAY', ':0')
    monkeypatch.setenv('PLAYWRIGHT_BROWSERS_PATH',str(tmp_path/'pinned-browser-cache'))
    worker(monkeypatch,tmp_path,"print(json.dumps({'result':{'running':True}}),flush=True)\nfor line in sys.stdin:\n request=json.loads(line)\n print(json.dumps({'result':{'keys':list(os.environ),'home':os.environ['HOME'],'config':os.environ['XDG_CONFIG_HOME'],'no_user_site':os.environ['PYTHONNOUSERSITE'],'browser_cache':os.environ.get('PLAYWRIGHT_BROWSERS_PATH'),'argv':sys.argv,'text':request.get('text')}}),flush=True)\n")
    assert commands.desktop_start() == {'running':True}
    state = Path(commands._STATE.name)
    assert state.stat().st_mode & 0o777 == 0o700
    reply = commands._request('type_text',text='private-$(_never_execute_)')
    assert {'OPENAI_API_KEY','ABX_SERVER_TOKEN','DISPLAY'}.isdisjoint(reply['keys'])
    assert reply['home'] == os.environ['HOME'] and reply['config'] == str(state/'config')
    assert reply['no_user_site']=='1' and 'private-' not in ' '.join(reply['argv'])
    assert reply['browser_cache']==str(tmp_path/'pinned-browser-cache')
    assert reply['text'] == 'private-$(_never_execute_)'
    assert commands._request('type_text',text='🙂'*4096)['text']=='🙂'*4096
    assert commands.desktop_start() == {'running':True,'reused':True}
    assert commands.desktop_stop() == 'stopped' and not state.exists()


@pytest.mark.parametrize('text',['x'*4096,'雪🙂'*2048])
def test_maximum_unicode_text_has_a_bounded_deadline(monkeypatch,text):
    calls=[]
    monkeypatch.setattr(commands,'_request',lambda *a,**kw:calls.append((a,kw)) or 'typed')
    assert commands.type_text(text)=='typed'
    assert calls[0][1]['text']==text and 0 < calls[0][1]['timeout'] <= 60


@pytest.mark.parametrize('mode',['stop','timeout','leader-exit','invalid-response'])
def test_cleanup_kills_real_redirected_descendants_without_touching_foreign_group(monkeypatch,tmp_path,mode):
    pidfile=tmp_path/'child.pid'
    child="import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(30)"
    body=("child=subprocess.Popen([sys.executable,'-c',"+repr(child)+"],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\n"
          "Path('child.pid').write_text(str(child.pid))\n"
          "print(json.dumps({'result':{'running':True}}),flush=True)\n"
          "line=sys.stdin.readline()\n")
    if mode=='leader-exit':body+='sys.exit(7)\n'
    elif mode=='invalid-response':body+="print('not-json',flush=True)\ntime.sleep(30)\n"
    else:body+='time.sleep(30)\n'
    foreign=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],start_new_session=True)
    try:
        worker(monkeypatch,tmp_path,body)
        commands.desktop_start();state=Path(commands._STATE.name)
        childpid=int(pidfile.read_text())
        if mode=='stop':commands.desktop_stop()
        else:
            with pytest.raises(RuntimeError):commands._request('fixture',timeout=1)
        assert not live(childpid) and foreign.poll() is None
        assert commands._PROCESS is None and not state.exists()
    finally:
        os.killpg(foreign.pid,signal.SIGKILL);foreign.wait()


def test_start_failure_removes_owned_state(monkeypatch,tmp_path):
    worker(monkeypatch,tmp_path,'sys.exit(1)\n')
    with pytest.raises(RuntimeError,match='unexpectedly'):commands.desktop_start()
    assert commands._PROCESS is None and commands._STATE is None


def test_python_cancellation_cleans_real_worker(monkeypatch,tmp_path):
    worker(monkeypatch,tmp_path,"print(json.dumps({'result':{'running':True}}),flush=True)\ntime.sleep(30)\n")
    commands.desktop_start();pid=commands._PROCESS.pid;state=Path(commands._STATE.name)
    monkeypatch.setattr(commands.select,'select',lambda *a: (_ for _ in ()).throw(KeyboardInterrupt()))
    with pytest.raises(KeyboardInterrupt):commands._response(2)
    assert not live(pid) and not state.exists()


@pytest.mark.parametrize('method,args',[(commands.click,(-1,0)),(commands.click,(0,768)),(commands.click,(True,0)),(commands.click,(1,1,'invalid')),(commands.type_text,('',)),(commands.type_text,('nul\x00',)),(commands.type_text,('\ud800',)),(commands.type_text,('a'*4097,)),(commands.hotkey,('ctrl,$(bad)',)),(commands.hotkey,('a,b,c,d,e',))])
def test_invalid_input_rejected_before_worker(monkeypatch,method,args):
    monkeypatch.setattr(commands,'_request',lambda *a,**k:pytest.fail('must not contact worker'))
    with pytest.raises(ValueError):method(*args)


def test_task_paths_cannot_escape_workspace_or_follow_external_symlink(monkeypatch,tmp_path):
    root=tmp_path/'workspace';root.mkdir();secret=tmp_path/'outside.json';secret.write_text('{}')
    (root/'escape.json').symlink_to(secret)
    monkeypatch.setenv('WORKSPACE',str(root))
    for path in ('../outside.json','escape.json'):
        with pytest.raises(ValueError):commands._task_path(path)
