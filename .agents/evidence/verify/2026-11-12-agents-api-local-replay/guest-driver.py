"""Actual private bridge/real Qwen turns; private config arrives only on stdin."""
import base64,collections,hashlib,http.client,json,os,pathlib,secrets,signal,sys,tempfile,threading,time
# Receive exactly one private input line, never echo or write it.
private=json.loads(sys.stdin.readline())
os.environ['OPENAI_API_KEY']=private.pop('apiKey')
os.environ['OPENAI_BASE_URL']=private.pop('baseUrl')
model=private.pop('model');assert model=='qwen3-coder-flash' and not private
from agent_sandbox.server.managed import ManagedBridge,make_bridge_server
workspace=pathlib.Path('/workspace/agents-api-demo')
original_tests=hashlib.sha256((workspace/'tests/test_aggregate.py').read_bytes()).hexdigest()
original_source=hashlib.sha256((workspace/'aggregate.py').read_bytes()).hexdigest()
assert 'totals[row["month"]] = Decimal(row["amount"])' in (workspace/'aggregate.py').read_text()
assert not (workspace/'outputs').exists()
started=time.monotonic();deadline=started+360
signal.alarm(375)
result={'scope':'local Docker private bridge + real Qwen model; not cloud/FC E2E','model':model,'turns':[]}
with tempfile.TemporaryDirectory(prefix='abx-real-qwen-state-') as tmp:
 bridge=ManagedBridge(tmp,str(workspace),max_file_bytes=262144,max_output_bytes=131072)
 token=secrets.token_hex(24);server=make_bridge_server(bridge,token,port=0)
 thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 def request(method,path,body=None):
  conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=15)
  try:
   headers={'Authorization':'Bearer '+token}
   data=json.dumps(body).encode() if body is not None else None
   if data is not None:headers['Content-Type']='application/json'
   conn.request(method,path,data,headers);response=conn.getresponse();raw=response.read(4*1024*1024)
   value=json.loads(raw)
   if response.status not in (200,201,202):raise RuntimeError('bridge_http_'+str(response.status)+'_'+str(value.get('error',{}).get('code')))
   return value
  finally:conn.close()
 try:
  session=request('POST','/managed/session',{'nonce':'local-two-turn-20261112','agent':{'adapter':'qwen-code','model':model}})
  prompts=[
   'Work in the existing workspace. Repair aggregate.py so repeated month rows accumulate with Decimal and months sort correctly. Preserve the exact original tests/test_aggregate.py and its CLI. Run python -m unittest discover -s tests -v and actually fix failures. Run python aggregate.py sales.csv outputs/summary.csv. Copy the repaired aggregate.py to outputs/aggregate.py. Do not implement --with-share yet. Do not change sales.csv. Finish only after executing the tools and verifying the CSV monthly totals are 30.00 and 10.00. Keep final reply short.',
   'Continue in this same workspace and preserve prior changes and the exact original tests. First read outputs/summary.csv from the prior turn; do not rewrite that file. Add --with-share support to aggregate.py while keeping ordinary mode compatible: output columns month,total,share and a four-decimal fractional share of the grand total. Run original unittest tests, then run python aggregate.py sales.csv outputs/shares.csv --with-share. Copy the final aggregate.py to outputs/aggregate.py. Write outputs/continuity.json containing first_summary_sha256 (actual SHA256 of the prior outputs/summary.csv bytes) and monthly_total_sum (string 40.00 computed from that prior CSV). Use actual file/command tools, verify shares 0.7500 and 0.2500, and give a short final reply.'
  ]
  first_summary_sha=None
  for index,prompt in enumerate(prompts,1):
   assert time.monotonic()<deadline
   rid='local_qwen_turn_'+str(index)
   request('POST','/managed/submissions',{'submission_id':rid,'session_id':session['session_id'],'input':prompt,'files':[],'deadline':time.time()+min(165,deadline-time.monotonic()),'max_tool_seconds':45,'max_output_bytes':131072,'max_events':2000})
   cursor=0;types=collections.Counter();wire_types=collections.Counter()
   while True:
    if time.monotonic()>deadline:raise TimeoutError('overall_deadline')
    state=request('GET','/managed/submissions/'+rid+'?after='+str(cursor))
    for event in state.get('events',[]):wire_types[event.get('wire',{}).get('type','unknown')]+=1
    cursor=state.get('returned_cursor',cursor)
    if state['status'] in ('completed','failed','cancelled','incomplete','uncertain') and cursor>=state.get('latest_cursor',cursor):break
    time.sleep(.5)
   items=state.get('items',[]);types.update(i.get('type','unknown') for i in items)
   tools=types['command_execution']+types['mcp_call']
   row={'index':index,'status':state['status'],'stopConfirmed':state.get('stop_confirmed'),'itemTypes':dict(types),'wireEventTypes':dict(wire_types),'toolItems':tools,'artifactErrors':state.get('artifact_errors',[])}
   if state['status']!='completed':
    row['errorCode']=state.get('error',{}).get('code') if isinstance(state.get('error'),dict) else None
    result['turns'].append(row);raise RuntimeError('turn_'+str(index)+'_'+state['status'])
   assert tools>0,'no_actual_tool_items'
   assert state.get('stop_confirmed') is True,'stop_not_confirmed'
   assert not state.get('artifact_errors')
   artifacts={a['path']:a for a in state.get('artifacts',[])}
   assert {'outputs/aggregate.py','outputs/summary.csv'}<=artifacts.keys()
   if index==1:first_summary_sha=artifacts['outputs/summary.csv']['sha256']
   else:
    assert artifacts['outputs/summary.csv']['sha256']==first_summary_sha,'prior_artifact_changed'
    assert {'outputs/shares.csv','outputs/continuity.json'}<=artifacts.keys()
   row['artifacts']=[{k:a[k] for k in ('path','sha256','bytes')} for a in artifacts.values()]
   result['turns'].append(row)
   # Only fixed expected public business artifacts leave this container.
   selected=('outputs/aggregate.py','outputs/summary.csv') if index==1 else ('outputs/aggregate.py','outputs/summary.csv','outputs/shares.csv','outputs/continuity.json')
   result['firstArtifacts' if index==1 else 'finalArtifacts']={name:artifacts[name] for name in selected}
  assert hashlib.sha256((workspace/'tests/test_aggregate.py').read_bytes()).hexdigest()==original_tests
  result.update(originalTestsUnchanged=True,originalSourceSha256=original_source,originalTestsSha256=original_tests,sameNativeSession=True,seconds=round(time.monotonic()-started,2))
 finally:
  for local in bridge.runtime.list_sessions():bridge.runtime.delete_session(local.id)
  server.shutdown();server.server_close();thread.join(timeout=5)
print(json.dumps(result))
