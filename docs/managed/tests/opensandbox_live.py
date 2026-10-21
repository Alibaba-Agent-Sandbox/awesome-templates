"""Real Docker/OpenSandbox interpreter acceptance on a dedicated, secret-free runner.

Server and client sources, provider and CLI are checked out at fixed revisions by CI.
This is native OpenSandbox acceptance, separate from Express source-template steps.
"""
from __future__ import annotations
import argparse,asyncio,contextlib,hashlib,importlib.metadata,json,logging,os,re,shlex,shutil,signal,subprocess,sys,threading,time,traceback,urllib.request,uuid
from datetime import timedelta
from pathlib import Path

PINS={'upstream':'30348cbdfe4b9cfd49e0963617aed357a8f1ac4c','provider':'9d2cf07467ff0e36303e4c80cbfe9fbf0fd70c6d','cli':'c8e8ad784323b8903505442cbc77d433a0d0367a','sdk':'33f857f5a79fd10326652e9d03f15f3621d6b848'}
RESULT={'provider':'opensandbox','template':'opensandbox-code-interpreter','template_id':'opensandbox/code-interpreter:v1.1.0','build_mode':'external-docker-image','passed':False,'cleanup_verified':False,'native_interpreter_verified':False,'pins':PINS,'checks':[]}

def check(value,label):
    if not value:
        RESULT.setdefault('failed_check',label)
        raise AssertionError(label)
    RESULT['checks'].append(label)

def safe_error(error):
    text=str(error).replace('fixed-synthetic-opensandbox-key','[FIXTURE_KEY]')
    text=re.sub(r'https?://\S+|/[A-Za-z0-9_.@%/+-]+','[LOCATION]',text)
    text=re.sub(r'\b[0-9a-fA-F-]{16,}\b','[ID]',text)
    return text[:400]

def docker_ids():
    return set(subprocess.check_output(['docker','ps','-aq','--no-trunc'],text=True).split())

def image(reference):
    data=json.loads(subprocess.check_output(['docker','image','inspect',reference],text=True))[0]
    assert data['Architecture']=='amd64'
    digest=next(value for value in data['RepoDigests']if value.startswith(reference.split(':')[0]+'@sha256:'))
    return {'requested':reference,'digest':digest,'image_id':data['Id'],'architecture':data['Architecture']}

async def exercise(work,image_uri,image_id):
    from agent_sandbox.api.sandbox import Sandbox
    from agent_sandbox.models.errors import SandboxNotFoundError,ProviderFeatureNotSupportedError
    from opensandbox import Sandbox as NativeSandbox
    from opensandbox.config import ConnectionConfig
    from code_interpreter import CodeInterpreter,SupportedLanguage
    baseline=docker_ids();nonce='managed-owned-'+uuid.uuid4().hex
    sb=native=interpreter=None;sid=None;owned_containers=set();cleanup_error=None
    try:
        sb=await Sandbox.create(provider='opensandbox',template=image_uri,timeout=600,cpu=2,memory=3072,
            envs={'PYTHON_VERSION':'3.11','JAVA_VERSION':'17','NODE_VERSION':'20','GO_VERSION':'1.24'},metadata={'verification':nonce})
        sid=sb.id;owned_containers=docker_ids()-baseline
        (work/'owned-intent.json').write_text(json.dumps({'id':sid,'metadata':nonce,'docker_ids':sorted(owned_containers)}))
        check(bool(sid)and sb.provider=='opensandbox','actual Agent Sandbox SDK create')
        check(bool(owned_containers),'independent Docker container observation')
        observed=json.loads(subprocess.check_output(['docker','inspect',*sorted(owned_containers)],text=True))
        check(any(sid in value['Name']and value['Image']==image_id for value in observed),'Docker identity matches the original interpreter digest')
        info=await sb.refresh_info()
        check(info.metadata.get('verification')==nonce,'owned metadata readback')
        value=await sb.commands.run("python3 -c 'print(6*7)'",timeout=30)
        check(value.exit_code==0 and value.stdout.strip()=='42','SDK real shell Python program')
        path='/tmp/'+nonce+'.txt';await sb.files.write(path,'owned-file\n')
        check(await sb.files.read(path)=='owned-file\n','SDK file write/read')
        await sb.files.remove(path);check(not await sb.files.exists(path),'SDK file removal readback')
        try:await sb.run_code('print(6*7)')
        except ProviderFeatureNotSupportedError as exc:check(exc.code=='E8004','generic native interpreter remains explicitly unsupported')
        else:raise AssertionError('generic interpreter must not imply native provider support')
        config=ConnectionConfig(domain='127.0.0.1:8080',protocol='http',api_key='fixed-synthetic-opensandbox-key',use_server_proxy=True,request_timeout=timedelta(seconds=60))
        native=await NativeSandbox.connect(sid,connection_config=config)
        check(native.id==sid,'original SDK connects to the same Agent Sandbox-created ID')
        interpreter=await CodeInterpreter.create(sandbox=native,ready_timeout=timedelta(seconds=120))
        check(await interpreter.is_healthy(),'original execd and Jupyter runtime health')
        first=await interpreter.codes.create_context(SupportedLanguage.PYTHON)
        second=await interpreter.codes.create_context(SupportedLanguage.PYTHON)
        check(bool(first.id)and bool(second.id)and first.id!=second.id,'two original interpreter contexts')
        execution=await interpreter.codes.run('owned_value=37\nowned_value',context=first)
        check(execution.error is None and execution.result and execution.result[0].text.strip()=='37','native Python execution')
        execution=await interpreter.codes.run('owned_value+5',context=first)
        check(execution.error is None and execution.result and execution.result[0].text.strip()=='42','native persistent context second call')
        execution=await interpreter.codes.run("'owned_value' in globals()",context=second)
        check(execution.error is None and execution.result and execution.result[0].text.strip()=='False','native context isolation')
        execution=await interpreter.codes.run("raise ValueError('owned program error')",context=first)
        check(execution.error is not None and 'ValueError'in str(execution.error),'native program exception is preserved')
        await interpreter.codes.delete_context(first.id);await interpreter.codes.delete_context(second.id)
        remaining=await interpreter.codes.list_contexts(SupportedLanguage.PYTHON)
        check(all(context.id not in [first.id,second.id]for context in remaining),'native context deletion readback')
        RESULT['native_interpreter_verified']=True
    finally:
        for close in [interpreter.aclose if interpreter else None,native.close if native else None]:
            if close:
                try:await close()
                except Exception as exc:cleanup_error=type(exc).__name__
        # An uncertain create can be reconciled only through the exact authored metadata.
        if sb is None:
            try:
                matches=[v for v in await Sandbox.list(provider='opensandbox')if v.metadata.get('verification')==nonce]
                if not matches:cleanup_error='unresolved_create'
                for candidate in matches:
                    await Sandbox.kill_by_id(candidate.sandbox_id,provider='opensandbox')
                    try:await Sandbox.get_info_by_id(candidate.sandbox_id,provider='opensandbox')
                    except SandboxNotFoundError:pass
                    else:cleanup_error='recovered_id_absence_unconfirmed'
            except Exception as exc:cleanup_error=type(exc).__name__
        else:
            try:await sb.kill()
            except Exception as exc:cleanup_error=type(exc).__name__
            finally:await sb.close()
        absence=sid is None
        for _ in range(60):
            if sid:
                try:await Sandbox.get_info_by_id(sid,provider='opensandbox')
                except SandboxNotFoundError:absence=True
                except Exception:pass
            docker_absence=not (owned_containers & docker_ids())
            if absence and docker_absence:break
            await asyncio.sleep(.5)
        # The job starts only this server; a new remaining container is uncertain cleanup.
        no_new_containers=not(docker_ids()-baseline)
        RESULT['cleanup_observations']={'sdk_not_found':absence,'known_docker_absence':docker_absence,'no_new_containers':no_new_containers,'cleanup_error':cleanup_error}
        RESULT['cleanup_verified']=absence and docker_absence and no_new_containers and cleanup_error is None
        check(RESULT['cleanup_verified'],'independent SDK NotFound and Docker container absence')
        if (work/'owned-intent.json').exists()and RESULT['cleanup_verified']:(work/'owned-intent.json').unlink()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--fixtures',type=Path,required=True);parser.add_argument('--work',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    fixtures=args.fixtures.resolve();work=args.work.resolve();work.mkdir(parents=True,exist_ok=True);work.chmod(0o700)
    if list(work.iterdir()):parser.error('work directory must be fresh and empty')
    home=work/'home';home.mkdir(exist_ok=True)
    os.environ['HOME']=str(home);os.environ['ABX_BIN']=shlex.join(['node',str(fixtures/'cli/dist/bin/abx.js')])
    os.environ.update(ABX_OPENSANDBOX_BASE_URL='http://127.0.0.1:8080',ABX_OPENSANDBOX_API_KEY='fixed-synthetic-opensandbox-key',OPEN_SANDBOX_USE_SERVER_PROXY='true')
    for key in ['ABX_SANDBOX_API_KEY','E2B_API_KEY','ABX_E2B_API_KEY','OPENAI_API_KEY']:os.environ.pop(key,None)
    logging.disable(logging.CRITICAL)
    server=None;failure=None;started=time.monotonic()
    with (work/'private-controller.log').open('w')as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        try:
            for name,revision in PINS.items():
                actual=subprocess.check_output(['git','-C',str(fixtures/('providers'if name=='provider'else name)),'rev-parse','HEAD'],text=True).strip()
                check(actual==revision,'fixed source '+name)
            runtime=image('opensandbox/code-interpreter:v1.1.0');execd=image('opensandbox/execd:v1.1.0');RESULT['images']={'interpreter':runtime,'execd':execd}
            config=work/'server.toml';config.write_text('[server]\nhost="127.0.0.1"\nport=8080\napi_key="fixed-synthetic-opensandbox-key"\n[runtime]\ntype="docker"\nexecd_image='+json.dumps(execd['digest'])+'\n[store]\ntype="sqlite"\npath='+json.dumps(str(work/'server.db'))+'\n[docker]\nnetwork_mode="bridge"\npublish_host="127.0.0.1"\n[ingress]\nmode="direct"\n');config.chmod(0o600)
            server=subprocess.Popen([str(fixtures/'upstream/server/.venv/bin/opensandbox-server'),'--config',str(config)],stdout=log,stderr=log,start_new_session=True,env={'PATH':os.environ['PATH'],'HOME':str(home),'LANG':'C.UTF-8'})
            for _ in range(120):
                if server.poll()is not None:raise RuntimeError('original server exited before health')
                try:
                    with urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=2)as response:
                        if response.status==200:break
                except OSError:pass
                time.sleep(.5)
            else:raise RuntimeError('original server health timeout')
            check(True,'fixed-source original OpenSandbox Docker server health')
            subprocess.run([sys.executable,'-m','agent_sandbox.providers','install',str(fixtures/'providers/opensandbox'),'--yes'],stdout=log,stderr=log,check=True)
            asyncio.run(exercise(work,runtime['digest'],runtime['image_id']))
            RESULT['versions']={name:importlib.metadata.version(name)for name in ['agent-sandbox-client','agent-sandbox-server','opensandbox','opensandbox-code-interpreter']}
        except Exception as exc:
            failure=type(exc).__name__;traceback.print_exc();RESULT['error_type']=failure;RESULT['error_message']=safe_error(exc)
        finally:
            try:
                # The SDK spawned the engine as this Python process's child. Reap it
                # concurrently so CLI stop does not mistake our zombie for a live engine.
                record=home/'.abx/engine.json';waiter=None
                if record.exists():
                    pid=int(json.loads(record.read_text())['pid'])
                    def reap():
                        try:os.waitpid(pid,0)
                        except ChildProcessError:pass
                    waiter=threading.Thread(target=reap,daemon=True);waiter.start()
                stopped=subprocess.run(shlex.split(os.environ['ABX_BIN'])+['provider','engine','stop'],stdout=log,stderr=log,timeout=15)
                if waiter:waiter.join(timeout=5)
                check(stopped.returncode==0 and(not waiter or not waiter.is_alive()),'owned local provider engine stopped and child reaped')
            except Exception as exc:failure=failure or type(exc).__name__
            if server:
                try:os.killpg(server.pid,signal.SIGTERM)
                except ProcessLookupError:pass
                try:server.wait(timeout=10)
                except subprocess.TimeoutExpired:os.killpg(server.pid,signal.SIGKILL);server.wait(timeout=5)
                check(server.poll()is not None,'owned local original server process stopped')
    RESULT['duration_s']=round(time.monotonic()-started,3);RESULT['passed']=failure is None and RESULT['native_interpreter_verified']and RESULT['cleanup_verified']and bool(RESULT['checks'])and 'failed_check'not in RESULT
    RESULT['controller_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(RESULT,indent=2)+'\n')
    if os.environ.get('GITHUB_ACTIONS')=='true':
        notice=json.dumps(RESULT,separators=(',',':')).replace('%','%25').replace('\r','%0D').replace('\n','%0A')
        print('::notice title=Sanitized native OpenSandbox receipt::'+notice,flush=True)
    print(json.dumps({'passed':RESULT['passed'],'checks':len(RESULT['checks']),'cleanup_verified':RESULT['cleanup_verified'],'error_type':failure}),flush=True)
    return 0 if RESULT['passed']else 1

if __name__=='__main__':raise SystemExit(main())
