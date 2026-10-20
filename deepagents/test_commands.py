"""Actual installed native DeepAgents with authored local protocol/tools, no real model."""
import importlib.util,http.server,json,os,threading,sys,time
from pathlib import Path
import pytest
s=importlib.util.spec_from_file_location('native_deepagents_commands',Path(__file__).with_name('commands.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
seen=[];state={}
class H(http.server.BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_POST(self):
  v=json.loads(self.rfile.read(int(self.headers['Content-Length'])));seen.append(v)
  if (state.get('write') or state.get('execute')) and not any(m.get('role')=='tool' for m in v.get('messages',[])):
   message={'role':'assistant','content':None,'tool_calls':[{'id':'literal-write','type':'function','function':{'name':'execute' if state.get('execute') else 'write_file','arguments':json.dumps({'command':state['execute']} if state.get('execute') else {'file_path':'/literal.txt','content':'authored bytes\n'})}}]};finish='tool_calls'
  else:message={'role':'assistant','content':'42'};finish='stop'
  body=json.dumps({'id':'fixture','object':'chat.completion','created':1,'model':'fixture','choices':[{'index':0,'message':message,'finish_reason':finish}],'usage':{'prompt_tokens':1,'completion_tokens':1,'total_tokens':2}}).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)

@pytest.fixture
def native(tmp_path,monkeypatch):
    seen.clear();state.clear();project=tmp_path/'project';project.mkdir();home=tmp_path/'caller-home';home.mkdir();(home/'sentinel').write_text('untouched')
    monkeypatch.setenv('WORKSPACE',str(project));monkeypatch.setenv('HOME',str(home));monkeypatch.setenv('DEEPAGENTS_API_KEY','synthetic-fixture-key');monkeypatch.setenv('DEEPAGENTS_MODEL','fixture')
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),H);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();monkeypatch.setenv('DEEPAGENTS_BASE_URL','http://127.0.0.1:'+str(server.server_port)+'/v1')
    try:yield project
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5)
        assert (home/'sentinel').read_text()=='untouched' and len(list(home.iterdir()))==1

@pytest.mark.parametrize('enabled',[False,True,False])
def test_actual_native_permissions_and_authored_write(native,enabled):
    assert c.deepagents_version()=='0.7.25' and c.deepagents_setup_check()['model_set']
    state['write']=enabled;result=c.deepagents('Return the authored response.',allow_tools=enabled,command_timeout=30)
    assert result['exit_code']==0 and '42' in result['stdout']
    names={x['function']['name'] for req in seen for x in req.get('tools',[])}
    assert names==set(['ls','read_file','write_file','edit_file','glob','grep','execute','delete'] if enabled else [])
    assert 'task' not in names
    if enabled:assert (native/'literal.txt').read_text()=='authored bytes\n'
    else:assert list(native.iterdir())==[]


def test_key_path_and_type_guards_prevent_native_model_request(native,monkeypatch):
    with pytest.raises(ValueError):c.deepagents('task',cwd='..')
    with pytest.raises(ValueError):c.deepagents('task',allow_tools='yes')
    with pytest.raises(ValueError):c.deepagents('task',command_timeout=True)
    with pytest.raises(ValueError):c.deepagents('x'*262145)
    monkeypatch.delenv('DEEPAGENTS_API_KEY')
    with pytest.raises(RuntimeError,match='required'):c.deepagents('task')
    assert not seen


def test_explicit_endpoint_and_missing_runtime_guards(native,monkeypatch):
    monkeypatch.setenv('DEEPAGENTS_BASE_URL','https://user:password@example.invalid/v1')
    with pytest.raises(ValueError):c.deepagents('task')
    monkeypatch.setenv('DEEPAGENTS_PYTHON','/missing/deepagents/python')
    assert c.deepagents_setup_check()['installed'] is False
    assert not seen

def test_actual_child_environment_output_deadline_and_descendant_cleanup(tmp_path):
    import secrets,signal
    env={'PATH':os.environ['PATH'],'HOME':str(tmp_path)}
    code,out,_=c.process.run([sys.executable,'-c','import os;print("GITHUB_TOKEN" in os.environ)'],cwd=tmp_path,env=env,timeout=2)
    assert code==0 and out=='False\n'
    before=time.monotonic()
    with pytest.raises(RuntimeError,match='timeout_s'):c.process.run([sys.executable,'-c','import time;time.sleep(60)'],cwd=tmp_path,env=env,timeout=1)
    assert time.monotonic()-before<8
    with pytest.raises(RuntimeError,match='256KiB'):c.process.run([sys.executable,'-c','print("x"*1000000)'],cwd=tmp_path,env=env,timeout=2)
    nonce=secrets.token_hex(12);pidfile=tmp_path/'pid';body='import os,sys,subprocess;from pathlib import Path;p=subprocess.Popen([sys.executable,"-c","import time;time.sleep(60)"],env=dict(os.environ,ABX_DEEPAGENTS_FIXTURE='+repr(nonce)+'),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);Path('+repr(str(pidfile))+').write_text(str(p.pid));raise SystemExit(7)'
    try:
        code,_,_=c.process.run([sys.executable,'-c',body],cwd=tmp_path,env=env,timeout=2);assert code==7
        pid=int(pidfile.read_text())
        try:state=Path('/proc',str(pid),'stat').read_text().split()[2]
        except FileNotFoundError:state='absent'
        assert state in ('absent','Z')
    finally:
        if pidfile.exists():
            pid=int(pidfile.read_text());fd=None
            try:
                fd=os.pidfd_open(pid)
                if ('ABX_DEEPAGENTS_FIXTURE='+nonce).encode() in Path('/proc',str(pid),'environ').read_bytes().split(b'\0'):signal.pidfd_send_signal(fd,signal.SIGKILL)
            except (FileNotFoundError,ProcessLookupError):pass
            finally:
                if fd is not None:os.close(fd)


def test_actual_native_execute_background_child_is_owned_and_reaped(native):
    import secrets,signal,shlex
    nonce=secrets.token_hex(12);pidfile=native/'child.pid'
    program='import os,subprocess,sys;from pathlib import Path;p=subprocess.Popen([sys.executable,"-c","import time;time.sleep(60)"],env=dict(os.environ,ABX_DEEP_NATIVE_FIXTURE='+repr(nonce)+'),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);Path('+repr(str(pidfile))+').write_text(str(p.pid));print("authored execution complete")'
    state['execute']=shlex.quote(sys.executable)+' -c '+shlex.quote(program)
    try:
        result=c.deepagents('Perform the authored execute response.',allow_tools=True,command_timeout=30)
        assert result['exit_code']==0
        pid=int(pidfile.read_text())
        try:state_after=Path('/proc',str(pid),'stat').read_text().split()[2]
        except FileNotFoundError:state_after='absent'
        assert state_after in ('absent','Z')
        assert any(m.get('role')=='tool' and 'authored execution complete' in str(m.get('content')) for req in seen for m in req.get('messages',[]))
    finally:
        if pidfile.exists():
            pid=int(pidfile.read_text());fd=None
            try:
                fd=os.pidfd_open(pid)
                if ('ABX_DEEP_NATIVE_FIXTURE='+nonce).encode() in Path('/proc',str(pid),'environ').read_bytes().split(b'\0'):signal.pidfd_send_signal(fd,signal.SIGKILL)
            except (FileNotFoundError,ProcessLookupError):pass
            finally:
                if fd is not None:os.close(fd)
