"""Original upstream text runner and independently replayable retail trajectory."""
from __future__ import annotations
import hashlib,json,logging,math,os,sys,tomllib
from pathlib import Path

SOURCE='fc0055dc4e0a316c3f83133267fbd6faaa770992'
ROOT=Path('/opt/tau2')
LIMIT=8*1024*1024


def upstream():
    if (ROOT/'SOURCE_REV').read_text().strip()!=SOURCE:raise RuntimeError('native source revision mismatch')
    if tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version']!='1.0.1':raise RuntimeError('native source version mismatch')
    from loguru import logger
    logger.remove();logging.disable(logging.CRITICAL)
    from tau2.run import get_tasks,run_single_task
    from tau2.data_model.simulation import SimulationRun,TextRunConfig
    from tau2.evaluator.evaluator import EvaluationType,evaluate_simulation
    import tau2.run
    if not Path(tau2.run.__file__).resolve().is_relative_to(ROOT/'src'):raise RuntimeError('native module provenance mismatch')
    return get_tasks,run_single_task,SimulationRun,TextRunConfig,EvaluationType,evaluate_simulation


def task_for(get_tasks,task_id):
    tasks=get_tasks('retail',task_ids=[task_id])
    if len(tasks)!=1:raise ValueError('unknown retail task')
    task=tasks[0]
    if task.evaluation_criteria.nl_assertions:raise ValueError('this slice excludes tasks requiring another LLM judge')
    return task


def scrub(value,secrets):
    if isinstance(value,str):
        for secret in secrets:
            if secret:value=value.replace(secret,'[REDACTED_MODEL_SETTING]')
        return value
    if isinstance(value,list):return[scrub(item,secrets)for item in value]
    if isinstance(value,dict):return{scrub(key,secrets)if isinstance(key,str)else key:scrub(item,secrets)for key,item in value.items()}
    return value


def summary(simulation):
    score=float(simulation.reward_info.reward)
    if not math.isfinite(score)or not 0<=score<=1:raise RuntimeError('invalid native score')
    if simulation.termination_reason.value not in ['agent_stop','user_stop']:raise RuntimeError('native simulation ended prematurely')
    messages=simulation.model_dump(mode='json').get('messages')or[]
    return {'score':score,'termination_reason':simulation.termination_reason.value,'message_count':len(messages),
        'assistant_messages':sum(item.get('role')=='assistant'for item in messages),
        'user_messages':sum(item.get('role')=='user'for item in messages),
        'tool_call_count':sum(len(item.get('tool_calls')or[])for item in messages)}


def execute(operation,data):
    get_tasks,run_single_task,SimulationRun,TextRunConfig,EvaluationType,evaluate_simulation=upstream()
    if operation=='version':
        tasks=get_tasks('retail')
        return {'native_version':'1.0.1','domain':'retail','task_count':len(tasks)}
    task=task_for(get_tasks,data['task_id'])
    if operation=='run':
        settings=data['settings'];os.environ['OPENAI_API_KEY']=settings['key']
        os.environ['OPENAI_BASE_URL']=settings['base'];os.environ['OPENAI_API_BASE']=settings['base']
        import litellm
        litellm.telemetry=False;litellm.success_callback=[];litellm.failure_callback=[]
        # Both native participants have an explicit compatible provider/base.
        arguments={'api_base':settings['base'],'timeout':60,'max_tokens':2048,'num_retries':0}
        config=TextRunConfig(domain='retail',agent='llm_agent',user='user_simulator',
            llm_agent='openai/'+settings['model'],llm_user='openai/'+settings['model'],
            llm_args_agent=dict(arguments),llm_args_user=dict(arguments),max_steps=data['max_steps'],max_errors=3,
            enforce_communication_protocol=True,auto_review=False,seed=42)
        simulation=run_single_task(config,task,seed=42,evaluation_type=EvaluationType.ALL,
            save_dir=Path(os.environ['HOME'])/'native-logs',auto_review=False)
        result=summary(simulation)
        value={'template':'tau2-bench','source_commit':SOURCE,'domain':'retail','task_id':task.id,
            'simulation':scrub(simulation.model_dump(mode='json'),[settings['key'],settings['base']])}
        raw=(json.dumps(value,ensure_ascii=False,allow_nan=False,indent=2)+'\n').encode()
        if len(raw)>LIMIT:raise RuntimeError('native trajectory exceeds8MiB artifact bound')
        path=Path(data['artifact'])
        with path.open('xb')as output:output.write(raw)
        return result|{'native_version':'1.0.1','source_commit':SOURCE,'domain':'retail','task_id':task.id,
            'artifact_path':str(path),'artifact_bytes':len(raw),'artifact_sha256':hashlib.sha256(raw).hexdigest()}
    if operation=='verify':
        raw=Path(data['artifact']).read_bytes()
        if len(raw)>LIMIT:raise ValueError('trajectory exceeds8MiB')
        value=json.loads(raw)
        if value.get('template')!='tau2-bench'or value.get('source_commit')!=SOURCE or value.get('domain')!='retail'or value.get('task_id')!=task.id:raise ValueError('trajectory provenance mismatch')
        simulation=SimulationRun.model_validate(value['simulation'])
        if simulation.task_id!=task.id:raise ValueError('inner trajectory task differs')
        result=summary(simulation)
        reward=evaluate_simulation(simulation,task,EvaluationType.ALL,solo_mode=False,domain='retail',strict_replay=True)
        if reward.reward!=result['score']:raise RuntimeError('independent native replay score differs')
        return result|{'replayed':True,'artifact_sha256':hashlib.sha256(raw).hexdigest(),'task_id':task.id}
    raise ValueError('unknown native operation')


if __name__=='__main__':
    try:
        operation=sys.argv[1]
        raw=sys.stdin.buffer.read(32769)
        if len(raw)>32768:raise ValueError('request exceeds32KiB')
        data=json.loads(raw)if raw.strip()else{}
        # Set model auth before upstream imports; no key is persisted in a profile.
        if operation=='run':
            os.environ['OPENAI_API_KEY']=data['settings']['key']
            os.environ['OPENAI_BASE_URL']=data['settings']['base'];os.environ['OPENAI_API_BASE']=data['settings']['base']
        print(json.dumps(execute(operation,data),allow_nan=False))
    except Exception as exc:
        error={'error_type':type(exc).__name__,'native_operation_failed':True}
        if operation=='version'and isinstance(exc,ModuleNotFoundError):error['missing_module']=exc.name
        print(json.dumps(error),file=sys.stderr)
        raise SystemExit(1)
