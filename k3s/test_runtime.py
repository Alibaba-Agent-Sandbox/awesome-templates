"""Authored fixed worker processes, not original Kubernetes, test ownership contracts."""
import fcntl,hashlib,importlib.util,json,os,socket,subprocess,sys,time
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('k3s_runtime_unit',Path(__file__).with_name('runtime.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
lspec=importlib.util.spec_from_file_location('k3s_listener_unit',Path(__file__).with_name('lifecycle.py'))
life=importlib.util.module_from_spec(lspec);lspec.loader.exec_module(life)

@pytest.mark.parametrize('value',['',' ',None,True,5,'x\0y','x'*32769])
def test_manifest_bounds_before_native_or_filesystem(value):
    with pytest.raises(ValueError):r.validate(value)

@pytest.mark.parametrize('value',[29,301,True,False,'30',None,1.5])
def test_deadline_is_bounded_integer(value):
    with pytest.raises(ValueError):r.validate('kind: Namespace',value)

def test_environment_never_inherits_operator_configuration(tmp_path,monkeypatch):
    for key in ['KUBECONFIG','K3S_URL','K3S_TOKEN','OPENAI_API_KEY','ABX_SERVER_TOKEN']:monkeypatch.setenv(key,'fixed-not-inherited')
    env=r.environment(tmp_path);assert all(key not in env for key in ['KUBECONFIG','K3S_URL','K3S_TOKEN','OPENAI_API_KEY','ABX_SERVER_TOKEN'])
    assert env['HOME']==str(tmp_path)and env['TMPDIR']==str(tmp_path)

@pytest.fixture
def worker(tmp_path,monkeypatch):
    node=tmp_path/'node';node.mkdir(mode=0o700);binary=tmp_path/'fixed-k3s'
    binary.write_text('#!'+sys.executable+'\n'+'''import json,os,pathlib,signal,socket,sys,time
args=sys.argv[1:]
def value(flag):return args[args.index(flag)+1]
if args==['--version']:print('k3s version v1.37.1+k3s1 (fixed-authored-worker)');raise SystemExit(0)
if '--help'in args:print('--config --data-dir --write-kubeconfig --https-listen-port');raise SystemExit(0)
if args[0]=='server':
 assert '--disable-agent'in args
 assert '--node-ip'in args and value('--node-ip')==value('--advertise-address')
 private=pathlib.Path(value('--data-dir')).parent;req=json.loads((private/'request.json').read_text());node=pathlib.Path(req['node_dir'])
 assert pathlib.Path(value('--config')).read_text()=='{}\\n'
 (node/'password').write_text('a'*32+'\\n');(node/'password').chmod(0o600)
 port=int(value('--https-listen-port'));s=socket.socket();s.bind(('0.0.0.0',port));s.listen()
 pathlib.Path(value('--write-kubeconfig')).write_text(json.dumps({'port':port}))
 pathlib.Path(__file__).with_name('observed.json').write_text(json.dumps({'pid':os.getpid(),'port':port,'private':str(private),'argv':args,'outer_owner':bool(os.environ.get('ABX_K3S_OWNER')),'rpc_owner':bool(os.environ.get('ABX_K3S_RPC_OWNER'))}))
 while True:time.sleep(.05)
assert args[0]=='kubectl'
config=json.loads(pathlib.Path(value('--kubeconfig')).read_text())
with socket.create_connection(('127.0.0.1',config['port']),timeout=1):pass
if '--raw'in args:print('ok')
elif 'nodes'in args:print(json.dumps({'kind':'NodeList','items':[]}))
elif 'create'in args:
 name=args[args.index('namespace')+1];assert '--dry-run=server'in args;print(json.dumps({'kind':'Namespace','metadata':{'name':name}}))
elif 'get'in args and'namespace'in args:
 name=args[args.index('namespace')+1];print('Error from server (NotFound): namespaces "'+name+'" not found',file=sys.stderr);raise SystemExit(1)
elif 'apply'in args:
 assert '--dry-run=server'in args and '--validate=strict'in args
 source=pathlib.Path(value('-f'));data=json.loads(source.read_text())
 if data.get('x-wait'):time.sleep(30)
 if data.get('x-infra'):print('error validating data: failed to download openapi: connection refused',file=sys.stderr);raise SystemExit(1)
 if data.get('x-stop'):
  state=json.loads(pathlib.Path(__file__).with_name('observed.json').read_text());os.kill(state['pid'],signal.SIGTERM);time.sleep(.1)
 if data.get('kind')=='Service'and not isinstance(data.get('spec',{}).get('ports'),list):
  print('error validating data: ValidationError(Service.spec.ports): invalid type, expected array',file=sys.stderr);raise SystemExit(1)
 print(json.dumps(data))
else:raise SystemExit(9)
''');binary.chmod(0o755)
    monkeypatch.setattr(r,'NODE_DIR',node);monkeypatch.setattr(r,'executable',lambda:str(binary));return node,binary

def namespace(**extra):return json.dumps({'apiVersion':'v1','kind':'Namespace','metadata':{'name':'authored-example'},**extra})

def assert_stopped(binary):
    state=json.loads(binary.with_name('observed.json').read_text());assert state['outer_owner']and not state['rpc_owner']
    assert not Path(state['private']).exists()
    assert not life._listener_exists(state['port'])
    proc=Path('/proc')/str(state['pid'])/'stat'
    assert not proc.exists()or proc.read_text().split()[2]=='Z'

@pytest.mark.skipif(os.geteuid()==0,reason='runtime contract refuses root')
def test_authored_original_shape_server_dryrun_proofs_and_complete_cleanup(worker):
    node,binary=worker;result=r.validate(namespace(),30)
    assert result['valid']and result['object']['kind']=='Namespace'and result['worker_nodes']==0
    assert all(result[x]is True for x in ['api_ready','post_api_ready','probe_not_persisted','api_server_stopped','private_state_removed','node_state_restored'])
    assert list(node.iterdir())==[];assert_stopped(binary)

@pytest.mark.skipif(os.geteuid()==0,reason='runtime contract refuses root')
def test_authored_native_validation_error_preserves_api_health(worker):
    node,binary=worker;value=r.validate(json.dumps({'apiVersion':'v1','kind':'Service','metadata':{'name':'authored-example'},'spec':{'ports':'invalid'}}),30)
    assert value['valid']is False and value['object']is None and 'expected array'in value['validation_error']
    assert value['post_api_ready']and value['api_server_stopped']and list(node.iterdir())==[];assert_stopped(binary)

@pytest.mark.skipif(os.geteuid()==0,reason='runtime contract refuses root')
@pytest.mark.parametrize('extra',[{'x-infra':True},{'x-stop':True}])
def test_infrastructure_or_postreturn_death_cannot_become_invalid_manifest_success(worker,extra):
    node,binary=worker
    with pytest.raises(RuntimeError,match='diagnostic_stage='):r.validate(namespace(**extra),30)
    assert list(node.iterdir())==[];assert_stopped(binary)

@pytest.mark.skipif(os.geteuid()==0,reason='runtime contract refuses root')
def test_outer_deadline_kills_nested_server_and_rpc_preserves_unrelated_process(worker,monkeypatch):
    node,binary=worker;actual=r.PROCESS.run
    monkeypatch.setattr(r.PROCESS,'run',lambda argv,**kwargs:actual(argv,**{**kwargs,'timeout':1.5}))
    outsider=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'])
    try:
        with pytest.raises(RuntimeError,match='timeout'):r.validate(namespace(**{'x-wait':True}),30)
        assert outsider.poll()is None and list(node.iterdir())==[];assert_stopped(binary)
    finally:outsider.terminate();outsider.wait(timeout=5)

@pytest.mark.skipif(os.geteuid()==0,reason='runtime contract refuses root')
@pytest.mark.parametrize('content',['FOREIGN','a'*32+'\n'])
def test_preexisting_node_state_is_preserved_even_when_shape_matches_native(worker,content):
    node,binary=worker;file=node/'password';file.write_text(content)
    with pytest.raises(RuntimeError,match='pre-existing'):r.validate(namespace(),30)
    assert file.read_text()==content and not binary.with_name('observed.json').exists()

@pytest.mark.skipif(os.geteuid()==0,reason='runtime contract refuses root')
def test_directory_lock_rejects_concurrent_server_without_mutation(worker):
    node,binary=worker;fd=os.open(node,os.O_RDONLY|os.O_DIRECTORY);fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    try:
        with pytest.raises(RuntimeError,match='another original'):r.validate(namespace(),30)
        assert list(node.iterdir())==[]and not binary.with_name('observed.json').exists()
    finally:os.close(fd)

@pytest.mark.parametrize('kind',['foreign-file','symlink','wrong-password'])
def test_cleanup_never_removes_foreign_node_state(tmp_path,kind):
    node=tmp_path/'node';node.mkdir(mode=0o700);foreign=tmp_path/'foreign';foreign.write_text('PRESERVE');fd=os.open(node,os.O_RDONLY|os.O_DIRECTORY)
    if kind=='foreign-file':(node/'id').write_text('PRESERVE')
    elif kind=='symlink':(node/'password').symlink_to(foreign)
    else:(node/'password').write_text('wrong')
    try:
        with pytest.raises(RuntimeError):r.cleanup_node_state(fd,0)
        assert foreign.read_text()=='PRESERVE'and len(list(node.iterdir()))==1
    finally:os.close(fd)
