"""Fixed metadata transport fixtures; no native CLI or generated source executes here."""
import importlib.util,json,threading,urllib.request,urllib.error
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import pytest
s=importlib.util.spec_from_file_location('claude_adapter_fixture',Path(__file__).with_name('relay.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)

def native(**extra):
 return {'model':'owned-model','stream':True,'max_tokens':99999,'system':[{'type':'text','text':'system'}],
         'messages':[{'role':'user','content':'fix'},{'role':'assistant','content':[{'type':'tool_use','id':'a','name':'Read','input':{'file_path':'calc.py'}}]},{'role':'user','content':[{'type':'tool_result','tool_use_id':'a','content':[{'type':'text','text':'code'}]}]}],
         'tools':[{'name':'Read','description':'read','input_schema':{'type':'object'}}],**extra}

def answer(tool=False):
 m={'role':'assistant','content':'DONE'}
 if tool:m['tool_calls']=[{'id':'call-owned','type':'function','function':{'name':'Edit','arguments':'{"file_path":"calc.py","old_string":"-","new_string":"+"}'}}]
 return {'choices':[{'message':m,'finish_reason':'tool_calls'if tool else'stop'}],'usage':{'prompt_tokens':9,'completion_tokens':3}}

def test_native_tool_history_preserved():
 x=r.request(native(),'owned-model');assert x['model']=='owned-model'and x['max_tokens']==8192 and x['stream']is False
 assert x['messages'][0]=={'role':'system','content':'system'}
 assert x['messages'][2]['tool_calls'][0]['id']=='a'and x['messages'][3]=={'role':'tool','tool_call_id':'a','content':'code'}
 assert x['tools'][0]['function']['parameters']=={'type':'object'}and x['parallel_tool_calls']is False

@pytest.mark.parametrize('patch',[{'model':'other'},{'stream':False},{'thinking':{'type':'enabled'}},{'messages':[{'role':'user','content':[{'type':'image'}]}]},{'tools':[{'name':'Task','input_schema':{}}]},{'tool_choice':{'type':'any'}},{'messages':[]}])
def test_unsupported_native_features_fail_closed(patch):
 with pytest.raises(ValueError):r.request(native(**patch),'owned-model')

@pytest.mark.parametrize('tool',[False,True])
def test_native_stream_shape_and_actual_usage(tool):
 x=r.reply(answer(tool),'owned-model');ev=list(r.events(x));assert ev[0][0]=='message_start'and ev[-1][0]=='message_stop'
 assert ev[-2][1]['usage']['output_tokens']==3 and x['usage']['input_tokens']==9
 assert x['stop_reason']==('tool_use'if tool else'end_turn')
 if tool:assert x['content'][-1]['input']['new_string']=='+'and x['content'][-1]['name']=='Edit'

@pytest.mark.parametrize('mutate',[lambda x:x['choices'][0].update(finish_reason='length'),lambda x:x.update(usage={}),lambda x:x['choices'][0]['message'].update(tool_calls=[{'id':'x','type':'function','function':{'name':'Task','arguments':'{}'}}]),lambda x:x['choices'][0]['message'].update(tool_calls=[{'id':'x','type':'function','function':{'name':'Read','arguments':'not-json'}}])])
def test_incomplete_or_unsupported_tool_response_rejected(mutate):
 x=answer();mutate(x)
 with pytest.raises((ValueError,TypeError)):r.reply(x,'owned-model')

@pytest.mark.parametrize('base',['https://example.test/v1?key=secret','https://a:b@example.test/v1','http://example.test/v1','https://example.test/v1#x','https://example.test:bad/v1'])
def test_private_credential_origin_guards(base):
 with pytest.raises(ValueError):r.settings(base,'key','model')


def test_real_http_owned_auth_translation_and_listener_cleanup():
 seen=[]
 class H(BaseHTTPRequestHandler):
  def do_POST(self):
   data=json.loads(self.rfile.read(int(self.headers['Content-Length'])));seen.append((self.path,self.headers.get('Authorization'),data))
   raw=json.dumps(answer(True)).encode();self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
  def log_message(self,*a):pass
 upstream=ThreadingHTTPServer(('127.0.0.1',0),H);thread=threading.Thread(target=upstream.serve_forever,daemon=True);thread.start();relay=r.Relay('http://127.0.0.1:'+str(upstream.server_port)+'/v1','upstream-only-key','owned-model',10)
 def post(path,token,data):
  return urllib.request.urlopen(urllib.request.Request(relay.url+path,data=json.dumps(data).encode(),headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'}),timeout=5)
 try:
  for path,token,data in [('/v1/messages','wrong',native()),('/other',relay.token,native()),('/v1/messages',relay.token,native(model='wrong'))]:
   with pytest.raises(urllib.error.HTTPError):post(path,token,data)
  assert seen==[]
  with post('/v1/messages?beta=true',relay.token,native())as response:
   raw=response.read().decode();assert 'message_stop'in raw and 'input_json_delta'in raw and 'upstream-only-key'not in raw
  relay.wait_for_idle();assert len(seen)==1 and seen[0][0]=='/v1/chat/completions'and seen[0][1]=='Bearer upstream-only-key'
  assert seen[0][2]['messages'][3]['role']=='tool'and relay.snapshot()=={'model_requests':1,'completed_responses':1,'failed_responses':0,'native_tool_calls':1,'native_tool_results':1}
 finally:relay.close();upstream.shutdown();upstream.server_close();thread.join(3)


def test_redirect_never_forwards_root_key():
 contacted=[]
 class H(BaseHTTPRequestHandler):
  def do_POST(self):
   contacted.append(self.path);self.send_response(302);self.send_header('Location','http://127.0.0.1:1/no');self.end_headers()
  def log_message(self,*a):pass
 up=ThreadingHTTPServer(('127.0.0.1',0),H);t=threading.Thread(target=up.serve_forever,daemon=True);t.start();relay=r.Relay('http://127.0.0.1:'+str(up.server_port),'root-key','owned-model',10)
 try:
  req=urllib.request.Request(relay.url+'/v1/messages',data=json.dumps(native()).encode(),headers={'Authorization':'Bearer '+relay.token})
  with pytest.raises(urllib.error.HTTPError)as exc:urllib.request.urlopen(req,timeout=5)
  assert exc.value.code==502;relay.wait_for_idle();assert contacted==['/chat/completions']and relay.snapshot()['failed_responses']==1
 finally:relay.close();up.shutdown();up.server_close();t.join(3)
