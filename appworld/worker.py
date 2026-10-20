"""Original AppWorld execution/evaluation with encrypted protected artifacts.

Only the disposable sandbox runs this worker. The model bridge is authored here;
original AppWorld APIs, execution guards, databases and evaluator are unchanged.
"""
import contextlib
import hashlib
import importlib.metadata
import io
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

BOOTSTRAP=Path('/opt/appworld-bootstrap')
STAGE='request'
META=None
BOOTSTRAP_ERROR=None
MISSING_MODULE=None
RUN_OBSERVATION={}
FAILURE_STREAM=sys.stderr


class NativeIncomplete(RuntimeError):
    pass


def identity():
    from install_data import verify_package
    meta=json.loads((BOOTSTRAP/'upstream.json').read_text())
    if meta['version']!='0.1.3.post1' or meta['source_commit']!='66ad8099e12188ece0d3fe45e661dbc01880813b':
        raise RuntimeError('unreviewed AppWorld identity')
    package=verify_package(meta)
    data=BOOTSTRAP/'data.bundle'
    with data.open('rb') as stream:
        if data.stat().st_size!=34280074 or hashlib.file_digest(stream,'sha256').hexdigest()!=meta['data']['sha256']:
            raise RuntimeError('original encrypted data differs')
    return meta,package



def copy_private_package(original,root):
    package=root/'appworld'
    shutil.copytree(original,package,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    # Layer/source modes can be read-only. This owned copy must support the
    # original installer, without relaxing public-source or private-HOME modes.
    package.chmod(0o700)
    for path in package.rglob('*'):
        if path.is_symlink():
            raise ValueError('native package source may not contain symlinks')
        path.chmod(0o700 if path.is_dir() else 0o600)
    return package


def bootstrap():
    global META,STAGE,BOOTSTRAP_ERROR,MISSING_MODULE
    STAGE='upstream'
    meta,original=identity()
    root=Path.cwd()/'private-package'
    root.mkdir(mode=0o700)
    STAGE='private_copy'
    package=copy_private_package(original,root)
    sys.path.insert(0,str(root))
    world_root=Path(os.environ['APPWORLD_ROOT'])
    world_root.mkdir(mode=0o700)
    # Run the original installer in its own interpreter. The engine must first
    # import after protected apps exist, avoiding stale app-discovery caches.
    install_env=dict(os.environ)
    install_env['PYTHONPATH']=str(root)
    STAGE='installer'
    with tempfile.TemporaryFile() as errors:
        installed=subprocess.run([sys.executable,'-m','appworld.cli','install'],env=install_env,
                   stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=errors,
                   timeout=90)
        if installed.returncode:
            errors.seek(0,2)
            errors.seek(max(0,errors.tell()-8192))
            text=errors.read().decode('utf-8','replace')
            names=re.findall(r'^([A-Za-z_][A-Za-z0-9_]{0,63}(?:Error|Exception)):',text,re.M)
            BOOTSTRAP_ERROR=names[-1] if names else 'NativeInstallerNonzero'
            missing=re.findall(r"^ModuleNotFoundError: No module named '([A-Za-z_][A-Za-z0-9_.]{0,127})'",text,re.M)
            MISSING_MODULE=missing[-1] if missing else None
            raise RuntimeError('original private installer failed; raw diagnostics omitted')
    from appworld.common.constants import PASSWORD,SALT
    from appworld.common.utils import unpack_bundle
    STAGE='data_unpack'
    unpack_bundle(str(BOOTSTRAP/'data.bundle'),str(world_root),PASSWORD,SALT)
    META=meta
    return world_root


def select_task(task):
    from appworld import load_task_ids
    tasks=load_task_ids('train')
    if not tasks:
        raise RuntimeError('native training inventory empty')
    chosen=task or tasks[0]
    if chosen not in tasks:
        raise ValueError('only original training task IDs are supported')
    return chosen,len(tasks)


def stats(tracker):
    count=tracker.num_tests
    passed=tracker.pass_count
    if type(count) is not int or count<=0 or type(passed) is not int or not 0<=passed<=count:
        raise RuntimeError('native evaluation counts invalid')
    return {'score':1.0 if tracker.success else 0.0,'success':bool(tracker.success),
            'num_tests':count,'pass_count':passed}


def api_log_count(world):
    world.save_logs()
    path=Path(world.output_logs_directory)/'api_calls.jsonl'
    return sum(bool(line.strip()) for line in path.read_text().splitlines())


def smoke():
    from appworld import AppWorld
    task,count=select_task('')
    with AppWorld(task_id=task,experiment_name='native_smoke',timeout_seconds=30) as world:
        output=world.execute('print(apis.api_docs.show_app_descriptions())')
        calls=api_log_count(world)
        if not output.strip() or output.startswith('Execution failed.') or calls<=0:
            raise RuntimeError('original native API smoke failed')
    return {'native_version':'0.1.3.post1','original_engine':True,'native_api_calls':calls,
            'training_task_count':count,'protected_state_private':True}


def model_run(request,root):
    global STAGE,RUN_OBSERVATION
    from appworld import AppWorld
    from appworld.common.constants import PASSWORD,SALT
    from appworld.common.utils import pack_bundle
    from openai import OpenAI
    task,count=select_task(request['task'])
    experiment='run_'+secrets.token_hex(16)
    settings=request['settings']
    # The key/base are private process memory from anonymous parent stdin.
    client=OpenAI(api_key=settings['key'],base_url=settings['base'],timeout=60,max_retries=0)
    tools=[{'type':'function','function':{'name':'inspect_api','description':'Read original allowed app/API documentation. Empty app lists apps; app without api lists APIs; app+api returns exact parameter documentation.','parameters':{'type':'object','properties':{'app':{'type':'string'},'api':{'type':'string'}},'required':[],'additionalProperties':False}}},
           {'type':'function','function':{'name':'call_api','description':'Call an original allowed AppWorld API using exact documented arguments. Login/password lookup and supervisor.complete_task are real APIs.','parameters':{'type':'object','properties':{'app':{'type':'string'},'api':{'type':'string'},'arguments':{'type':'object'}},'required':['app','api','arguments'],'additionalProperties':False}}}]
    messages=[]
    model_steps=0
    bridge_calls=0
    RUN_OBSERVATION={'model_steps':0,'bridge_api_calls':0,'native_api_calls':0,'tool_validation_failures':0}
    STAGE='world_init'
    try:
        with AppWorld(task_id=task,experiment_name=experiment,max_interactions=160,
                      max_api_calls_per_interaction=50,timeout_seconds=30) as world:
            messages=[{'role':'system','content':'Complete the original AppWorld training task using only inspect_api and call_api. Read actual API parameter documentation before calling. Use supervisor APIs to obtain simulated account information. Finish through supervisor.complete_task, with answer when required. No ground-truth solutions are supplied. Never invent IDs, credentials, API names or results.'},
                      {'role':'user','content':json.dumps({'instruction':world.task.instruction,
                          'supervisor':dict(world.task.supervisor),'apps':world.task.app_descriptions},ensure_ascii=False)}]
            allowed=world.task.api_docs
            complete=False
            for _ in range(request['max_steps']):
                if len(json.dumps(messages,ensure_ascii=False).encode())>1024*1024:
                    raise NativeIncomplete('native model context bound reached')
                STAGE='model_request'
                response=client.chat.completions.create(model=settings['model'],messages=messages,
                    tools=tools,tool_choice='auto',temperature=0,max_tokens=4096)
                if not response.id or not response.choices:
                    raise NativeIncomplete('native model response incomplete')
                model_steps+=1
                RUN_OBSERVATION['model_steps']=model_steps
                message=response.choices[0].message
                calls=message.tool_calls or []
                item={'role':'assistant','content':message.content or ''}
                if calls:
                    item['tool_calls']=[{'id':call.id,'type':call.type,'function':{'name':call.function.name,'arguments':call.function.arguments}} for call in calls]
                messages.append(item)
                if len(calls)>16:
                    raise NativeIncomplete('model tool call bound exceeded')
                if not calls:
                    messages.append({'role':'user','content':'Use the actual APIs and finish the task with supervisor.complete_task.'})
                    continue
                for call in calls:
                    if call.type!='function' or len(call.function.arguments.encode())>32768:
                        raise NativeIncomplete('invalid bounded model tool call')
                    try:
                        STAGE='tool_validation'
                        params=json.loads(call.function.arguments)
                        if not isinstance(params,dict):
                            raise ValueError('tool parameters must be an object')
                        app=params.get('app','')
                        api=params.get('api','')
                        if call.function.name=='inspect_api':
                            if set(params)-{'app','api'}:
                                raise ValueError('unknown inspect arguments')
                            if not app:
                                result=world.task.app_descriptions
                            elif app not in allowed:
                                raise ValueError('app outside original task scope')
                            elif not api:
                                result={name:value['description'] for name,value in allowed[app].items()}
                            elif api in allowed[app]:
                                result=allowed[app][api]
                            else:
                                raise ValueError('unknown original API')
                            output=json.dumps(result,ensure_ascii=False)
                        elif call.function.name=='call_api':
                            if set(params)!={'app','api','arguments'} or not isinstance(params['arguments'],dict):
                                raise ValueError('invalid API arguments')
                            if not all(isinstance(name,str) and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,100}',name) for name in [app,api]):
                                raise ValueError('invalid API identifier')
                            if app not in allowed or api not in allowed[app]:
                                raise ValueError('API outside original task scope')
                            # JSON arguments become Python literals, never executable model code.
                            STAGE='native_api'
                            output=world.execute(f'print(apis.{app}.{api}(**{params["arguments"]!r}))')
                            bridge_calls+=1
                            RUN_OBSERVATION['bridge_api_calls']=bridge_calls
                        else:
                            raise ValueError('unknown tool')
                    except (ValueError,TypeError,KeyError):
                        RUN_OBSERVATION['tool_validation_failures']+=1
                        output='Invalid tool parameters or API scope; inspect the original documentation and retry.'
                    messages.append({'role':'tool','tool_call_id':call.id,'content':output[:32768]})
                    STAGE='native_completion_check'
                    if world.task_completed():
                        complete=True
                        break
                if complete:
                    break
            STAGE='native_completion_check'
            RUN_OBSERVATION['native_api_calls']=api_log_count(world)
            if not complete or model_steps<=0 or bridge_calls<=0:
                raise NativeIncomplete('original task did not complete')
            native_calls=api_log_count(world)
            if native_calls<=0:
                raise NativeIncomplete('original native API calls absent')
            STAGE='summary'
            summary=stats(world.evaluate(suppress_errors=False))
        metadata={'format':'appworld-native-protected-result-v1','native_version':'0.1.3.post1',
                  'source_commit':META['source_commit'],'data_sha256':META['data']['sha256'],
                  'task':task,'experiment':experiment,'model':settings['model'],
                  'model_steps':model_steps,'bridge_api_calls':bridge_calls,
                  'native_api_calls':native_calls,'task_completed':True,**summary}
        directory=root/'abx_metadata'
        directory.mkdir()
        (directory/'result.json').write_text(json.dumps(metadata,sort_keys=True))
        # Native task/code/database outputs remain protected and encrypted.
        STAGE='artifact'
        artifact=Path(request['artifact'])
        pack_bundle(str(artifact),str(root),['experiments/outputs/'+experiment,'abx_metadata'],PASSWORD,SALT)
        artifact.chmod(0o600)
        if not 0<artifact.stat().st_size<=64*1024*1024:
            raise RuntimeError('encrypted native result exceeds64MiB')
        with artifact.open('rb') as stream:
            digest=hashlib.file_digest(stream,'sha256').hexdigest()
        return {**metadata,'artifact_path':str(artifact),'log_path':str(artifact),
                'artifact_bytes':artifact.stat().st_size,'artifact_sha256':digest,
                'training_task_count':count,'artifact_encrypted':True}
    finally:
        client.close()


def verify(request,root):
    global STAGE
    from appworld.common.constants import PASSWORD,SALT
    from appworld.common.utils import decrypt_bytes
    from appworld.evaluator import evaluate_task
    STAGE='replay'
    source=Path(request['artifact'])
    with source.open('rb') as stream:
        encrypted=stream.read(64*1024*1024+1)
    if len(encrypted)>64*1024*1024:
        raise ValueError('encrypted artifact exceeds64MiB')
    plain=decrypt_bytes(encrypted,PASSWORD,SALT)
    with zipfile.ZipFile(io.BytesIO(plain)) as archive:
        members=archive.infolist()
        if len(members)>4096 or sum(item.file_size for item in members)>512*1024*1024:
            raise ValueError('native result expansion exceeds reviewed bound')
        metadata=json.loads(archive.read('abx_metadata/result.json'))
        experiment=metadata['experiment']
        if not re.fullmatch(r'run_[a-f0-9]{32}',experiment):
            raise ValueError('invalid native experiment ownership')
        for item in members:
            path=PurePosixPath(item.filename)
            if path.is_absolute() or '..' in path.parts or stat.S_ISLNK(item.external_attr>>16):
                raise ValueError('invalid native result member')
            if not (item.filename.startswith('experiments/outputs/'+experiment+'/') or item.filename.startswith('abx_metadata/')):
                raise ValueError('native result member outside owned experiment')
        archive.extractall(root)
    task,_=select_task(request['task'] or metadata['task'])
    if (metadata.get('format')!='appworld-native-protected-result-v1' or metadata.get('task')!=task
            or metadata.get('source_commit')!=META['source_commit'] or metadata.get('data_sha256')!=META['data']['sha256']
            or metadata.get('native_version')!='0.1.3.post1' or metadata.get('task_completed') is not True):
        raise ValueError('native result provenance or task mismatch')
    observed=stats(evaluate_task(task_id=task,experiment_name=experiment,suppress_errors=False,save_report=False))
    if any(observed[key]!=metadata.get(key) for key in ['score','success','num_tests','pass_count']):
        raise ValueError('independent original evaluator differs from saved result')
    return {'verified':True,'task':task,'original_evaluator':True,'model_credentials_used':False,**observed}


def main():
    global STAGE
    request=json.load(sys.stdin)
    operation=sys.argv[1]
    if operation=='version':
        meta,_=identity()
        return {'native_version':meta['version'],'source_commit':meta['source_commit'],
                'data_sha256':meta['data']['sha256'],'protected_bundles_encrypted':True}
    with open(os.devnull,'w') as quiet,contextlib.redirect_stdout(quiet):
        root=bootstrap()
        STAGE='task'
        if operation=='smoke':
            return smoke()
        if operation=='run':
            return model_run(request,root)
        if operation=='verify':
            return verify(request,root)
        raise ValueError('unknown operation')


if __name__=='__main__':
    try:
        result=main()
        print(json.dumps(result,ensure_ascii=False))
    except Exception as exc:
        print('\nABX_APPWORLD_FAILURE '+json.dumps({'error_type':type(exc).__name__,'native_stage':STAGE,'bootstrap_error_type':BOOTSTRAP_ERROR,'missing_module':MISSING_MODULE,'native_counters':RUN_OBSERVATION,'http_status':getattr(exc,'status_code',None)}),file=FAILURE_STREAM,flush=True)
        raise SystemExit(1)
