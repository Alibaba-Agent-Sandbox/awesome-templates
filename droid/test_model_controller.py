"""Native NDJSON terminal-result and local generated-code execution guards."""
import importlib.util
import json
from pathlib import Path
import pytest
s=importlib.util.spec_from_file_location('droid_owned_acceptance_controller',Path(__file__).with_name('e2e_test.py'))
c=importlib.util.module_from_spec(s)
s.loader.exec_module(c)


def test_exact_native_terminal_result_required():
    value={'type':'result','subtype':'success','is_error':False,'num_turns':2,'result':'fresh marker','session_id':'session'}
    assert c.final_text(json.dumps(value))=='fresh marker'
    assert c.final_text(json.dumps(value|{'result':'fresh marker\nnot final'}))!='fresh marker'
    for change in [{'type':'progress'},{'subtype':'failure'},{'num_turns':0},{'num_turns':True},{'session_id':''},{'is_error':True}]:
        assert c.final_text(json.dumps(value|change))==''
    assert c.final_text('fresh marker')==''
    assert c.final_text(json.dumps(value)+'\n'+json.dumps(value))==''


@pytest.mark.parametrize('base',['http://127.0.0.1:9000','http://127.0.0.2:9000','http://0.0.0.0:9000','http://localhost:9000','http://[::1]:9000','http://[::ffff:127.0.0.1]:9000'])
def test_controller_never_executes_generated_code_on_operator_loopback(monkeypatch,base):
    monkeypatch.setenv('E2E_RUN_LLM','1');monkeypatch.setenv('E2E_REMOTE_SANDBOX','1');c.RESULTS.clear()
    c.model_check(None,'/tmp',base);assert c.RESULTS==[False]


def test_actual_sdk_named_command_serialization_and_bearer_separation(monkeypatch):
    from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
    import threading
    requests=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*_):pass
        def do_POST(self):
            value=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append((self.path,self.headers.get('Authorization'),self.headers.get('X-Access-Token'),value))
            body=json.dumps({'result':{'native_version':'0.241.1','exit_code':0,'stdout':'authored fixture'}}).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    monkeypatch.setenv('E2E_SERVER_TOKEN','synthetic-server-token')
    try:
        params={'prompt':'fixed authored fixture','cwd':'/owned/project','command_timeout':30}
        value=c.native_sdk_command('http://127.0.0.1:'+str(server.server_port),params)
        assert value['exit_code']==0
        assert requests==[('/commands/droid_byok','Bearer synthetic-server-token',None,params)]
    finally:server.shutdown();server.server_close();thread.join(timeout=5)
