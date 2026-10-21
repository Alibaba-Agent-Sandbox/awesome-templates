"""Fixed GenerateContent/Chat fixtures; no original native or generated code locally."""
import importlib.util,json,threading,urllib.request,urllib.error
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import pytest
s=importlib.util.spec_from_file_location('gemini_owned_adapter',Path(__file__).with_name('relay.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)

def native():
 return {'systemInstruction':{'parts':[{'text':'system'}]},'contents':[{'role':'user','parts':[{'text':'fix'}]},{'role':'model','parts':[{'functionCall':{'name':'read_file','args':{'file_path':'calc.py'},'id':'call-owned'}}]},{'role':'user','parts':[{'text':'reminder'},{'functionResponse':{'name':'read_file','id':'call-owned','response':{'output':'code'}}}]}],
         'tools':[{'functionDeclarations':[{'name':'read_file','description':'read','parameters':{'type':'OBJECT','properties':{'file_path':{'type':'STRING'}},'required':['file_path']}}]}],'generationConfig':{'maxOutputTokens':4096}}

def answer(tool=False):
 m={'role':'assistant','content':'DONE'}
 if tool:m['tool_calls']=[{'id':'new-call','type':'function','function':{'name':'replace','arguments':'{"file_path":"calc.py","old_string":"-","new_string":"+"}'}}]
 return {'choices':[{'message':m,'finish_reason':'tool_calls'if tool else'stop'}],'usage':{'prompt_tokens':9,'completion_tokens':3}}

def test_original_function_ids_results_and_user_reminder_order():
 x=r.request(native(),'owned-model');assert [m['role']for m in x['messages']]==['system','user','assistant','tool','user']
 assert x['messages'][2]['tool_calls'][0]['id']==x['messages'][3]['tool_call_id']=='call-owned'
 assert x['tools'][0]['function']['parameters']=={'type':'object','properties':{'file_path':{'type':'string'}},'required':['file_path']}
 assert x['stream']is False and x['parallel_tool_calls']is False

def test_native_optional_function_ids_correlate_by_original_history():
 x=native();del x['contents'][1]['parts'][0]['functionCall']['id'];del x['contents'][2]['parts'][1]['functionResponse']['id']
 y=r.request(x,'owned');assert y['messages'][2]['tool_calls'][0]['id']==y['messages'][3]['tool_call_id']=='call_1_0'

@pytest.mark.parametrize('part',[{'inlineData':{'mimeType':'image/png','data':'fixed'}},{'text':'secret','thought':True},{'functionCall':{'name':'delegate_to_agent','args':{}}},{'functionResponse':{'name':'other','response':{}}}])
def test_unknown_native_content_refused(part):
 x=native();x['contents'][0]['parts']=[part]
 with pytest.raises(ValueError):r.request(x,'owned')

@pytest.mark.parametrize('kind',['thinking','unknown_tool','wrong_id','incomplete'])
def test_unsupported_native_profiles_rejected(kind):
 x=native()
 if kind=='thinking':x['generationConfig']['thinkingConfig']={'thinkingBudget':100}
 elif kind=='unknown_tool':x['tools'][0]['functionDeclarations'][0]['name']='delegate_to_agent'
 elif kind=='wrong_id':x['contents'][2]['parts'][1]['functionResponse']['id']='wrong'
 else:x['contents']=[]
 with pytest.raises(ValueError):r.request(x,'owned')

@pytest.mark.parametrize('tool',[False,True])
def test_original_google_response_and_real_usage_shape(tool):
 x=r.reply(answer(tool),'owned');assert x['usageMetadata']=={'promptTokenCount':9,'candidatesTokenCount':3,'totalTokenCount':12}and x['modelVersion']=='owned'
 assert x['candidates'][0]['finishReason']=='STOP'and list(r.events(x))==[('',x)]
 if tool:assert x['candidates'][0]['content']['parts'][-1]['functionCall']['name']=='replace'

@pytest.mark.parametrize('finish',['length','content_filter',None])
def test_truncated_model_reply_rejected(finish):
 x=answer();x['choices'][0]['finish_reason']=finish
 with pytest.raises(ValueError):r.reply(x,'owned')

@pytest.mark.parametrize('base',['http://example.test/v1','https://x:y@example.test/v1','https://example.test/v1?q=x','https://example.test/v1#x'])
def test_approved_origin_only(base):
 with pytest.raises(ValueError):r.settings(base,'key','model')


def test_actual_http_original_google_route_auth_and_owned_cleanup():
 seen=[]
 class H(BaseHTTPRequestHandler):
  def do_POST(self):
   x=json.loads(self.rfile.read(int(self.headers['Content-Length'])));seen.append((self.path,self.headers.get('Authorization'),x));raw=json.dumps(answer(True)).encode();self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
  def log_message(self,*a):pass
 up=ThreadingHTTPServer(('127.0.0.1',0),H);t=threading.Thread(target=up.serve_forever,daemon=True);t.start();relay=r.Relay('http://127.0.0.1:'+str(up.server_port)+'/v1','root-only','owned-model',10)
 def post(path,token):
  return urllib.request.urlopen(urllib.request.Request(relay.url+path,data=json.dumps(native()).encode(),headers={'Authorization':'Bearer '+token}),timeout=5)
 try:
  for path,token in [('/v1beta/models/owned-model:streamGenerateContent?alt=sse','bad'),('/v1beta/models/other:streamGenerateContent?alt=sse',relay.token),('/v1/messages',relay.token)]:
   with pytest.raises(urllib.error.HTTPError):post(path,token)
  assert not seen
  with post('/v1beta/models/owned-model:streamGenerateContent?alt=sse',relay.token)as response:
   text=response.read().decode();assert text.startswith('data: {')and 'functionCall'in text and 'root-only'not in text
  relay.wait_for_idle();assert seen[0][0]=='/v1/chat/completions'and seen[0][1]=='Bearer root-only'and seen[0][2]['model']=='owned-model'
  assert relay.snapshot()['completed_responses']==1 and relay.snapshot()['failed_responses']==0 and relay.snapshot()['native_tool_calls']==1
 finally:relay.close();up.shutdown();up.server_close();t.join(3)


def test_explicit_native_disabled_thinking_preserves_text_tool_profile():
    value=native();value['generationConfig']['thinkingConfig']={'includeThoughts':False,'thinkingBudget':0}
    result=r.request(value,'owned-model');assert result['model']=='owned-model'and result['tools'][0]['function']['name']=='read_file'
