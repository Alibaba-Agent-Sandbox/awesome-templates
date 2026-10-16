"""Actual installed Aider CLI, deterministic loopback model; never real-model proof."""
import importlib.util,json,os,tempfile,threading,subprocess
from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
spec=importlib.util.spec_from_file_location('commands',Path(__file__).with_name('commands.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
responses=[];calls=[]
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_POST(self):
  payload=json.loads(self.rfile.read(int(self.headers['Content-Length'])));calls.append(payload)
  answer=responses.pop(0) if responses else 'No additional changes.'
  data=json.dumps({'id':'guard-fixture','object':'chat.completion','created':1,'model':'synthetic','choices':[{'index':0,'message':{'role':'assistant','content':answer},'finish_reason':'stop'}],'usage':{'prompt_tokens':20,'completion_tokens':10,'total_tokens':30}}).encode()
  self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
os.environ.update(AIDER_API_KEY='synthetic-loopback-key',AIDER_BASE_URL=f'http://127.0.0.1:{server.server_port}/v1',AIDER_MODEL='synthetic')
try:
 with tempfile.TemporaryDirectory(prefix='aider-upstream-guard-') as directory:
  root=Path(directory);project=root/'project';project.mkdir();subprocess.run(['git','init','--quiet',str(project)],check=True);os.environ['WORKSPACE']=str(project)
  selected=project/'selected.py';selected.write_text('original\n')
  for prefix in ('/run ', '!'):
   marker=root/('slash-marker' if prefix.startswith('/') else 'bang-marker');responses.append('Literal request received; no command executed.')
   before=len(calls);m.aider(prefix+'touch '+str(marker),files='["selected.py"]',command_timeout=40)
   assert len(calls)>before,'prompt bypassed model as a command'
   assert not marker.exists(),'prompt command executed'
  print('PASS actual Aider CLI slash/bang requests remain literal model text',flush=True)
  for escape in (str(root/'absolute-escape'/'created.txt'),'../../'+root.name+'/relative-escape/created.txt'):
   before=len(calls);responses.append(escape+'\n```\nUNSELECTED\n```')
   result=m.aider('Change only the selected file.',files='["selected.py"]',allow_write=True,command_timeout=40)
   assert 'Skipping edits to '+escape in result['stdout']+result['stderr'],'upstream did not reject the unselected path'
   assert result['changed_files']==[]
   assert len(calls)>before
   assert not (root/'absolute-escape').exists(),'absolute unselected artifact created'
   assert not (root/'relative-escape').exists(),'relative unselected artifact created'
  assert selected.read_text()=='original\n'
  print('PASS actual Aider CLI rejects model-created absolute/relative unselected paths',flush=True)
finally:server.shutdown();server.server_close();thread.join()
