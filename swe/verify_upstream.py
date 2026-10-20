"""Actual installed official mini CLI + deterministic upstream model controls.

No external model/network. This proves CLI-loop observation and fatal timeout
propagation, not real-model coding or benchmark results.
"""
import json
import os
from pathlib import Path
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
import commands as c
from swe_process import run


def native_protocol_check(root):
    """Actual installed mini and deterministic native HTTP; not model acceptance."""
    seen=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            native=any(tool.get('function',{}).get('name')=='bash' for tool in body.get('tools',[]));seen.append(native)
            message={'role':'assistant','content':'This deterministic endpoint requires native bash tool calls.'}
            if native:
                message={'role':'assistant','content':None,'tool_calls':[{'id':'owned-fixture-call','type':'function','function':{'name':'bash','arguments':json.dumps({'command':'echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT'})}}]}
            response={'id':'owned-fixture','object':'chat.completion','created':0,'model':'fixture','choices':[{'index':0,'message':message,'finish_reason':'tool_calls' if native else 'stop'}],'usage':{'prompt_tokens':1,'completion_tokens':1,'total_tokens':2}}
            payload=json.dumps(response).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    workspace=root/'native-workspace';workspace.mkdir();run_id='a'*32;target=workspace/'.swe-runs'/run_id;(target/'repo').mkdir(parents=True)
    try:
        with patch.dict(os.environ,{'WORKSPACE':str(workspace),'SWE_MODEL_PROTOCOL':'toolcall','SWE_API_KEY':'synthetic-native-protocol-key','SWE_BASE_URL':'http://127.0.0.1:'+str(server.server_port)+'/v1','SWE_MODEL':'fixture'}):
            try:
                result=c.swe_run_agent(run_id,allow_execution=True,max_steps=3,command_timeout=30)
                assert result['exit_status']=='Submitted' and result['model_calls']==1 and seen==[True]
            finally:c.swe_cleanup(run_id)
    finally:
        server.shutdown();server.server_close();thread.join(timeout=5);assert not thread.is_alive()
    print('PASS actual official mini CLI advertises native bash tool schema, executes deterministic action and submits in one call',flush=True)


def message(command):
    return {'role':'assistant','content':'owned deterministic control','extra':{'actions':[{'command':command}],'cost':0}}


def invoke(root, name, outputs, timeout=1):
    folder=root/name;folder.mkdir(mode=0o700);trajectory=folder/'trajectory.json'
    config={'run':{'task':'owned deterministic adapter regression'},
        'agent':{'agent_class':'default','system_template':'Execute the provided task.','instance_template':'{{task}}','step_limit':4,'cost_limit':0,'output_path':str(trajectory)},
        'model':{'model_class':'deterministic','model_name':'deterministic','outputs':[message(command) for command in outputs]},
        'environment':{'environment_class':'swe_environment.OwnedLocalEnvironment','cwd':str(folder),'timeout':timeout,'env':{'PATH':'/usr/bin:/bin'}}}
    config_path=folder/'config.yaml';config_path.write_text(json.dumps(config));config_path.chmod(0o600)
    env=c._environment()|{'PYTHONPATH':str(c.HERE),'MSWEA_GLOBAL_CONFIG_DIR':str(folder/'config'),'MSWEA_CONFIGURED':'true','MSWEA_SILENT_STARTUP':'1'}
    code,out,err=run([c.MINI,'-c',str(config_path),'-o',str(trajectory)],cwd=str(folder),env=env,timeout=20)
    return code,json.loads(trajectory.read_text())


def main():
    with tempfile.TemporaryDirectory(prefix='swe-official-guards-') as temporary:
        root=Path(temporary)
        native_protocol_check(root)
        code,state=invoke(root,'observation',["printf 'héllo\\n'; printf 'stderr\\n' >&2; exit 7",'echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT'])
        assert code==0 and state['info']['exit_status']=='Submitted'
        observations=[m.get('content','') for m in state['messages'] if m.get('role')=='user']
        assert any('héllo' in m and 'stderr' in m and '<returncode>7</returncode>' in m for m in observations),'CLI lost actual action output/nonzero'
        print('PASS actual official CLI propagates Unicode stdout/stderr and nonzero action result',flush=True)
        pid_file=root/'child.pid';after=root/'must-not-run'
        code,state=invoke(root,'timeout',['sleep 60 & echo $! > '+str(pid_file)+'; wait','touch '+str(after)])
        assert code!=0 and state['info']['exit_status']=='RuntimeError' and state['info']['model_stats']['api_calls']==1,'CLI swallowed environment timeout and continued'
        assert not after.exists(),'CLI continued after fatal action timeout'
        pid=int(pid_file.read_text());stat=Path('/proc')/str(pid)/'stat'
        try:state_code=stat.read_text().split()[2]
        except FileNotFoundError:state_code='absent'
        assert state_code in ('absent','Z'),'ordinary action child survived owned CLI cleanup'
        print('PASS actual official CLI fatal action timeout stops loop and owned child is absent or exited',flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
