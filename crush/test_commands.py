"""Actual upstream binary with authored HTTP/process fixtures; no real-model evidence."""
import importlib.util,http.server,json,os,sys,threading,time
from pathlib import Path
import pytest
s=importlib.util.spec_from_file_location('crush_native_commands',Path(__file__).with_name('commands.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
seen=[];state={}
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_POST(self):
  value=json.loads(self.rfile.read(int(self.headers['Content-Length'])));seen.append(value)
  write_call=bool(value.get('stream') and state.get('write') and value.get('tools') and not any(m.get('role')=='tool' for m in value.get('messages',[])))
  if write_call:
   chunk={'id':'fixture','object':'chat.completion.chunk','created':1,'model':'fixture','choices':[{'index':0,'delta':{'role':'assistant','tool_calls':[{'index':0,'id':'authored-write','type':'function','function':{'name':'write','arguments':json.dumps({'file_path':'literal.txt','content':'authored deterministic bytes\n'})}}]},'finish_reason':None}]}
   final={'id':'fixture','object':'chat.completion.chunk','created':1,'model':'fixture','choices':[{'index':0,'delta':{},'finish_reason':'tool_calls'}]}
   body=('data: '+json.dumps(chunk)+'\n\ndata: '+json.dumps(final)+'\n\ndata: [DONE]\n\n').encode();kind='text/event-stream'
  elif value.get('stream'):
   body=('data: '+json.dumps({'id':'fixture','object':'chat.completion.chunk','created':1,'model':'fixture','choices':[{'index':0,'delta':{'role':'assistant','content':'42'},'finish_reason':None}]})+'\n\ndata: '+json.dumps({'id':'fixture','object':'chat.completion.chunk','created':1,'model':'fixture','choices':[{'index':0,'delta':{},'finish_reason':'stop'}],'usage':{'prompt_tokens':1,'completion_tokens':1,'total_tokens':2}})+'\n\ndata: [DONE]\n\n').encode();kind='text/event-stream'
  else:body=json.dumps({'id':'fixture','object':'chat.completion','created':1,'model':'fixture','choices':[{'index':0,'message':{'role':'assistant','content':'42'},'finish_reason':'stop'}],'usage':{'prompt_tokens':1,'completion_tokens':1,'total_tokens':2}}).encode();kind='application/json'
  self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)

@pytest.fixture
def native(tmp_path,monkeypatch):
    seen.clear();state.clear();root=tmp_path/'project';root.mkdir();home=tmp_path/'caller-home';home.mkdir();(home/'sentinel').write_text('unchanged')
    monkeypatch.setenv('WORKSPACE',str(root));monkeypatch.setenv('HOME',str(home));monkeypatch.setenv('CRUSH_API_KEY','synthetic-private-key');monkeypatch.setenv('CRUSH_MODEL','fixture')
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();monkeypatch.setenv('CRUSH_BASE_URL','http://127.0.0.1:'+str(server.server_port)+'/v1')
    try:yield root
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5)
        assert (home/'sentinel').read_text()=='unchanged' and len(list(home.iterdir()))==1

@pytest.mark.parametrize('enabled',[False,True])
def test_actual_native_permissions_and_literal_stdin(native,enabled):
    assert c.crush_version()=='0.98.1' and c.crush_setup_check()['model_set']
    result=c.crush('Return42. Literal stdin: $(this-is-never-a-shell)\n',allow_tools=enabled,command_timeout=30)
    assert result['exit_code']==0 and '42' in result['stdout']
    names={tool['function']['name'] for request in seen for tool in request.get('tools',[])}
    assert names==set(c.CODING_TOOLS if enabled else []) and not list(native.iterdir())


def test_actual_native_authored_write_tool(native):
    state['write']=True
    result=c.crush('Perform the deterministic tool response then finish.',allow_tools=True,command_timeout=30)
    assert result['exit_code']==0 and (native/'literal.txt').read_text()=='authored deterministic bytes\n'
    assert any(m.get('role')=='tool' for req in seen for m in req.get('messages',[]))

@pytest.mark.parametrize('name',['.crushrc','crushrc','.crush.json','crush.json'])
def test_caller_configuration_is_refused_before_native_request(native,name):
    p=native/name;p.write_text('caller bytes must remain')
    with pytest.raises(ValueError,match='caller Crush'):c.crush('test',allow_tools=True)
    assert p.read_text()=='caller bytes must remain' and not seen


def test_parent_git_root_configuration_is_refused(native):
    (native/'.git').mkdir();(native/'crush.json').write_text('caller parent config');child=native/'child';child.mkdir()
    with pytest.raises(ValueError,match='caller Crush'):c.crush('test',cwd=str(child))
    assert not seen


def test_missing_key_paths_and_limits_prevent_request(native,monkeypatch):
    with pytest.raises(ValueError):c.crush('test',cwd='..')
    with pytest.raises(ValueError):c.crush('test',command_timeout=True)
    with pytest.raises(ValueError):c.crush('test',allow_tools='yes')
    monkeypatch.delenv('CRUSH_API_KEY')
    with pytest.raises(RuntimeError,match='required'):c.crush('test')
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
    nonce=secrets.token_hex(12);pidfile=tmp_path/'pid';body='import os,sys,subprocess;from pathlib import Path;p=subprocess.Popen([sys.executable,"-c","import time;time.sleep(60)"],env=dict(os.environ,ABX_CRUSH_FIXTURE='+repr(nonce)+'),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);Path('+repr(str(pidfile))+').write_text(str(p.pid));raise SystemExit(7)'
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
                if ('ABX_CRUSH_FIXTURE='+nonce).encode() in Path('/proc',str(pid),'environ').read_bytes().split(b'\0'):signal.pidfd_send_signal(fd,signal.SIGKILL)
            except (FileNotFoundError,ProcessLookupError):pass
            finally:
                if fd is not None:os.close(fd)
