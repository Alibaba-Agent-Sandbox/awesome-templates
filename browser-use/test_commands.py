"""Actual native browser-use/Chromium with authored HTTP/JSON actions, no real model."""
import importlib.util,http.server,json,os,threading
from pathlib import Path
import pytest
s=importlib.util.spec_from_file_location('browser_use_commands',Path(__file__).with_name('commands.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
seen=[];counter=[];clicks=[];blocked={}
class H(http.server.BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def do_GET(self):
  if self.path=='/clicked':clicks.append(True);body=b'clicked';kind='text/plain'
  elif self.path=='/visited':counter.append(True);body=b'OK';kind='text/plain'
  else:body=b'<html><title>Native browser proof</title><h1>fixture42</h1><button onclick="fetch(\'/clicked\')">OwnedClick</button><script>fetch("/visited")</script></html>';kind='text/html'
  self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 def do_POST(self):
  data=json.loads(self.rfile.read(int(self.headers['Content-Length'])));seen.append(data)
  if blocked:
   blocked['entered'].set();blocked['release'].wait(15)
  import re
  content={'evaluation_previous_goal':'Success','memory':'Native fixture page visited','next_goal':'Finish','action':[{'done':{'text':'fixture42','success':True}}]}
  if not clicks:
   text='\n'.join(str(m.get('content')) for m in data.get('messages',[]));match=re.search(r'\[(\d+)\]<button[^\n]*\n\s*OwnedClick',text)
   if not match:raise RuntimeError('authored click target index unavailable')
   content['action']=[{'click':{'index':int(match[1])}}]

  body=json.dumps({'id':'fixture','object':'chat.completion','created':1,'model':'fixture','choices':[{'index':0,'message':{'role':'assistant','content':json.dumps(content)},'finish_reason':'stop'}],'usage':{'prompt_tokens':1,'completion_tokens':1,'total_tokens':2}}).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)

@pytest.fixture
def native(tmp_path,monkeypatch):
    seen.clear();counter.clear();clicks.clear();project=tmp_path/'project';project.mkdir();home=tmp_path/'caller-home';home.mkdir();(home/'sentinel').write_text('untouched')
    monkeypatch.setenv('WORKSPACE',str(project));monkeypatch.setenv('HOME',str(home));monkeypatch.setenv('BROWSER_USE_API_KEY','synthetic-fixture-key');monkeypatch.setenv('BROWSER_USE_MODEL','fixture')
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),H);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base='http://127.0.0.1:'+str(server.server_port);monkeypatch.setenv('BROWSER_USE_BASE_URL',base+'/v1')
    try:yield project,base
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5)
        assert (home/'sentinel').read_text()=='untouched' and len(list(home.iterdir()))==1


def test_real_keyless_native_version_cdp_navigation_png_and_cleanup(native):
    assert c.browser_use_version()=='0.13.11'
    assert c.browser_use_setup_check()['browser_installed'] is True
    assert c.browser_use_self_test()=='BROWSER_USE_NATIVE_OK'
    assert not seen


def test_real_native_authored_click_independent_counter_png_and_action_surface(native):
    from PIL import Image
    project,base=native;result=c.browser_use('Click OwnedClick then finish.',url=base+'/page',max_steps=3,command_timeout=60)
    assert result['done'] and result['success'] and result['result']=='fixture42' and result['final_url']==base+'/page'
    assert len(clicks)==1 and len(counter)==1 and len(seen)==2
    assert all('response_format' not in request for request in seen)
    # Native schema is explicitly placed in the upstream system prompt for compatible text responses.
    assert any('navigate' in str(m.get('content')) and 'json' in str(m.get('content')).lower() for req in seen for m in req.get('messages',[]) if m.get('role')=='system')
    path=Path(result['screenshot_path']);assert path.parent==project/'browser-use-artifacts' and path.stat().st_size==result['bytes']>1000
    with Image.open(path) as im:assert im.format=='PNG' and im.width>=900 and im.height>=600
    path.unlink()


def test_key_url_types_step_and_artifact_guards_prevent_native_model_request(native,monkeypatch):
    project,base=native
    for params in [{'task':'x','max_steps':True},{'task':'x','max_steps':21},{'task':'x','command_timeout':True},{'task':'x','url':'file:///etc/passwd'},{'task':'x','url':'https://user:pass@example.invalid/'},{'task':'x'*262145}]:
        with pytest.raises(ValueError):c.browser_use(**params)
    outside=project/'caller';outside.mkdir();(project/'browser-use-artifacts').symlink_to(outside,target_is_directory=True)
    with pytest.raises(ValueError,match='symlink'):c.browser_use('x')
    assert list(outside.iterdir())==[]
    monkeypatch.delenv('BROWSER_USE_API_KEY')
    with pytest.raises(RuntimeError,match='required'):c.browser_use('x')
    assert not seen


def test_runtime_pin_cannot_be_replaced_by_another_browser(native,monkeypatch):
    monkeypatch.setenv('BROWSER_USE_BROWSER_BINARY','/usr/bin/true')
    assert c.browser_use_setup_check()['browser_installed'] is False
    with pytest.raises(RuntimeError,match='pinned'):c.browser_use_self_test()
    assert not seen


def test_actual_native_timeout_removes_partial_artifact_and_owned_chromium(native):
    project,base=native
    with pytest.raises(RuntimeError):c.browser_use('x',url=base+'/page',command_timeout=1)
    assert list((project/'browser-use-artifacts').iterdir())==[]


def test_actual_overlapping_browser_operation_fails_busy_and_preserves_active_call(native):
    project,base=native;errors=[];results=[];blocked.update(entered=threading.Event(),release=threading.Event())
    def active():
        try:results.append(c.browser_use('Click OwnedClick then finish.',url=base+'/page',command_timeout=60))
        except BaseException as exc:errors.append(exc)
    thread=threading.Thread(target=active,daemon=True);thread.start()
    try:
        assert blocked['entered'].wait(20)
        with pytest.raises(RuntimeError,match='another browser-use operation'):c.browser_use_self_test()
    finally:
        blocked['release'].set();thread.join(timeout=40);blocked.clear()
    assert not thread.is_alive() and not errors and len(results)==1 and results[0]['success'] is True
    assert len(clicks)==1;Path(results[0]['screenshot_path']).unlink()


def test_native_error_summary_redacts_before_truncation_and_bounds_bytes():
    spec=importlib.util.spec_from_file_location('browser_error_worker',Path(__file__).with_name('worker.py'))
    worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
    settings={'api_key':'synthetic-private-value','base_url':'https://model.example.invalid/v1'}
    result=worker.error_summary([settings['api_key']+' '+settings['base_url']+' '+('中文'*1000)]*30,settings)
    assert len(result)==20 and all(len(x.encode('utf-8'))<=1024 for x in result)
    assert all(settings['api_key'] not in x and settings['base_url'] not in x for x in result)
    assert all('[REDACTED]' in x for x in result)
