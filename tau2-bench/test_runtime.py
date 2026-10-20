"""Authored process/guard/artifact contracts; no native benchmark/model claim."""
import importlib.util,json,os,sys
from pathlib import Path
from types import SimpleNamespace
import pytest


def load(name,file):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
c=load('tau2_commands_boundary_tests','commands.py');w=load('tau2_worker_boundary_tests','worker.py');e=load('tau2_controller_boundary_tests','e2e_test.py')


@pytest.fixture
def configured(tmp_path,monkeypatch):
    root=tmp_path/'project';root.mkdir();monkeypatch.setattr(c,'_ROOT',root);monkeypatch.setattr(c,'_CONFIG',{'MODEL_API_KEY':'synthetic-key-only','MODEL_BASE_URL':'https://model.example.invalid/v1','MODEL':'fixture-model'});return root


@pytest.mark.parametrize('params',[{'domain':'other'},{'task_id':'../0'},{'max_steps':True},{'max_steps':61},{'command_timeout':False},{'command_timeout':901}])
def test_invalid_requests_never_reach_native_or_model(configured,monkeypatch,params):
    monkeypatch.setattr(c,'_invoke',lambda *a:pytest.fail('invalid input reached native'))
    with pytest.raises(ValueError):c.tau2_run(**params)


@pytest.mark.parametrize('key,value',[('MODEL_API_KEY',''),('MODEL_API_KEY','bad\nkey'),('MODEL_BASE_URL','http://remote.invalid'),('MODEL_BASE_URL','https://u:p@remote.invalid'),('MODEL_BASE_URL','https://@remote.invalid'),('MODEL_BASE_URL','https://remote.invalid:bad'),('MODEL','--unsafe')])
def test_invalid_model_config_fails_before_network(configured,key,value):
    c._CONFIG[key]=value
    with pytest.raises(ValueError):c._config()


def test_environment_drops_operator_credentials(configured,tmp_path,monkeypatch):
    for key in ['GITHUB_TOKEN','ALICLOUD_ACCESS_KEY_SECRET','OPENAI_API_KEY','TAU2_MODEL_API_KEY','TAU2_BINARY']:monkeypatch.setenv(key,'unrelated-operator-secret')
    env=c._environment(tmp_path)
    assert not any(key in env for key in ['GITHUB_TOKEN','ALICLOUD_ACCESS_KEY_SECRET','OPENAI_API_KEY','TAU2_MODEL_API_KEY','TAU2_BINARY'])
    assert env['LITELLM_LOCAL_MODEL_COST_MAP']=='True'and env['TAU2_DATA_DIR']=='/opt/tau2/data'


@pytest.mark.parametrize('exit_code',[0,23])
def test_actual_authored_process_private_stdin_no_secret_env_and_cleanup(configured,tmp_path,monkeypatch,exit_code):
    capture=tmp_path/'capture.json';fixture=tmp_path/'authored_worker.py'
    fixture.write_text('import json,os,pathlib,sys\n'+f'pathlib.Path({str(capture)!r}).write_text(json.dumps({{"stdin":sys.stdin.read(),"argv":sys.argv,"env":dict(os.environ),"home":os.environ["HOME"]}}))\n'+f'print(json.dumps({{"safe":True}}));raise SystemExit({exit_code})\n')
    monkeypatch.setattr(c,'_runtime',lambda:(sys.executable,str(fixture)))
    if exit_code:
        with pytest.raises(RuntimeError,match='native Tau2 operation failed'):c.tau2_run()
        assert list(configured.iterdir())==[]
    else:assert c.tau2_run()=={'safe':True}
    value=json.loads(capture.read_text());assert 'synthetic-key-only'in value['stdin']
    assert 'synthetic-key-only'not in json.dumps(value['argv'])+json.dumps(value['env'])
    assert not Path(value['home']).exists()


def test_verification_refuses_resolved_symlink_escape(configured,tmp_path,monkeypatch):
    outside=tmp_path/'outside.json';outside.write_text('{}');(configured/'link').symlink_to(outside)
    monkeypatch.setattr(c,'_invoke',lambda*a:pytest.fail('escaped file reached native'))
    with pytest.raises(ValueError):c.tau2_verify_artifact('link')


def test_busy_version_cannot_replace_active_owner():
    c._LOCK.acquire()
    try:
        with pytest.raises(RuntimeError,match='active'):c.tau2_version()
    finally:c._LOCK.release()


def test_nested_artifact_scrubbing_covers_private_values_and_keys():
    value={'private-base':{'messages':['key-only',{'url':'private-base/path'}]}}
    result=w.scrub(value,['private-base','key-only']);encoded=json.dumps(result)
    assert 'private-base'not in encoded and'key-only'not in encoded


@pytest.mark.parametrize('reason',['max_steps','agent_error','infrastructure_error'])
def test_incomplete_native_simulation_cannot_return_a_score(reason):
    sim=SimpleNamespace(reward_info=SimpleNamespace(reward=1.0),termination_reason=SimpleNamespace(value=reason))
    with pytest.raises(RuntimeError,match='prematurely'):w.summary(sim)


@pytest.mark.parametrize('base',['http://127.0.0.1:9000','http://0.0.0.0:9000','http://localhost:9000','http://[::1]:9000','http://[::ffff:127.0.0.1]:9000'])
def test_model_controller_refuses_operator_target(monkeypatch,base):
    monkeypatch.setenv('E2E_RUN_LLM','1');monkeypatch.setenv('E2E_REMOTE_SANDBOX','1');e.RESULTS.clear();e.model(None,base,'/tmp');assert e.RESULTS==[False]


def test_actual_sdk_scalar_serialization_and_separate_bearer(monkeypatch):
    import asyncio,threading
    from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
    received=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_POST(self):
            value=json.loads(self.rfile.read(int(self.headers['Content-Length'])));received.append((self.path,self.headers.get('Authorization'),self.headers.get('X-Access-Token'),value));body=b'{"result":{"score":0.75}}';self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();monkeypatch.setenv('E2E_SERVER_TOKEN','synthetic-server-token')
    try:
        value=asyncio.run(e.native('http://127.0.0.1:'+str(server.server_port),'tau2_run',domain='retail',task_id='0',max_steps=30,command_timeout=600));assert value=={'score':0.75}
        assert received==[('/commands/tau2_run','Bearer synthetic-server-token',None,{'domain':'retail','task_id':'0','max_steps':30,'command_timeout':600})]
    finally:server.shutdown();server.server_close();thread.join(timeout=5)


def test_saved_reward_cannot_replace_independent_native_replay(tmp_path,monkeypatch):
    artifact=tmp_path/'trajectory.json';artifact.write_text(json.dumps({'template':'tau2-bench','source_commit':w.SOURCE,'domain':'retail','task_id':'0','simulation':{'task_id':'0'}}))
    task=SimpleNamespace(id='0',evaluation_criteria=SimpleNamespace(nl_assertions=[]))
    sim=SimpleNamespace(task_id='0',reward_info=SimpleNamespace(reward=1.0),termination_reason=SimpleNamespace(value='agent_stop'),model_dump=lambda**k:{'messages':[]})
    model=SimpleNamespace(model_validate=lambda value:sim)
    evaluate=lambda *a,**k:SimpleNamespace(reward=0.0)
    monkeypatch.setattr(w,'upstream',lambda:(lambda *a,**k:[task],None,model,None,SimpleNamespace(ALL='all'),evaluate))
    with pytest.raises(RuntimeError,match='replay score differs'):w.execute('verify',{'task_id':'0','artifact':str(artifact)})
