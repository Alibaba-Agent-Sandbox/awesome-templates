"""HTTP contract checks; require actual target runtime/model when explicitly requested."""
import base64
import json
import os
from pathlib import Path
import sys
import httpx
FAILED = 0
MODEL_TIMEOUT = int(os.environ.get('E2E_COMMAND_TIMEOUT', '600'))
if not 30 <= MODEL_TIMEOUT <= 900:
    raise ValueError('E2E_COMMAND_TIMEOUT must be from30 to900 seconds')


def enabled(name):
    return os.environ.get(name, '').lower() in ('1', 'true', 'yes')


def record(ok, label):
    global FAILED
    FAILED += not ok
    print(f"[{'PASS' if ok else 'FAIL'}] {label}", flush=True)


def valid_evaluation(evaluation):
    manifest=json.loads((Path(__file__).parent/'instance.json').read_text())
    return (evaluation.get('resolved_slice') is True and evaluation.get('official_benchmark_score') is False
        and evaluation.get('passed')==60 and not any(evaluation.get(k,1) for k in ('failed','errors','skipped'))
        and evaluation.get('fail_to_pass')==dict.fromkeys(manifest['fail_to_pass'],'passed')
        and evaluation.get('pass_to_pass')==dict.fromkeys(manifest['pass_to_pass'],'passed'))


def valid_baseline(baseline):
    manifest=json.loads((Path(__file__).parent/'instance.json').read_text())
    return (baseline.get('failed')==1 and baseline.get('passed')==59
        and baseline.get('errors')==0 and baseline.get('skipped')==0
        and baseline.get('fail_to_pass')==dict.fromkeys(manifest['fail_to_pass'],'failed')
        and baseline.get('pass_to_pass')==dict.fromkeys(manifest['pass_to_pass'],'passed'))


def acceptance(client):
    value=client.post('/commands/swe_setup_check',json={})
    setup=value.json().get('result',{}) if value.status_code==200 else {}
    wanted=enabled('E2E_RUN_LLM') or enabled('E2E_REQUIRE_LLM')
    if os.environ.get('E2E_RUN_LLM')=='0':wanted=False
    available=all(setup.get(k) is True for k in ('api_key_set','base_url_set','model_set','runtime_available'))
    if not wanted or not available:
        if enabled('E2E_REQUIRE_LLM'):record(False,'required real mini run cannot skip missing target settings/runtime')
        else:print('[SKIP] real mini coding; no model/image acceptance claimed',flush=True)
        return
    run_id=None
    try:
        response=client.post('/commands/swe_prepare',json={},timeout=240)
        record(response.status_code==200,'real pinned instance baseline prepared')
        if response.status_code!=200:return
        prepared=response.json()['result'];run_id=prepared['run_id'];baseline=prepared['baseline']
        baseline_ok=valid_baseline(baseline)
        record(baseline_ok,'real exact declared failing/passing baseline reproduced')
        if not baseline_ok:return
        response=client.post('/commands/swe_run_agent',json={'run_id':run_id,'allow_execution':True,'max_steps':30,'command_timeout':MODEL_TIMEOUT},timeout=MODEL_TIMEOUT+60)
        record(response.status_code==200 and response.json().get('result',{}).get('model_calls',0)>0,'genuine mini CLI real model submits')
        if response.status_code!=200:return
        response=client.post('/commands/swe_evaluate',json={'run_id':run_id},timeout=240)
        record(response.status_code==200,'independent evaluator completes')
        if response.status_code!=200:return
        evaluation=response.json()['result']
        record(valid_evaluation(evaluation),'original 60 test identities pass in fresh checkout/venv')
        record(evaluation['official_benchmark_score'] is False,'local portability slice is not an official benchmark score')
        response=client.get('/files/download-stream',params={'path':evaluation['patch_path']})
        patch=base64.b64decode(response.json()['content_base64']).decode() if response.status_code==200 else ''
        record('src/flask/blueprints.py' in patch and len(patch)>80,'nonempty source patch retrieved from remote files API')
        response=client.get('/files/download-stream',params={'path':evaluation['report_path']})
        report=json.loads(base64.b64decode(response.json()['content_base64'])) if response.status_code==200 else {}
        record(valid_evaluation(report),'independent report artifact retrieved')
    finally:
        if run_id:
            response=client.post('/commands/swe_cleanup',json={'run_id':run_id})
            record(response.status_code==200 and response.json().get('result') is True,'owned instance workdir cleaned')


def main():
    token=os.environ.get('E2E_TOKEN','');headers={'Authorization':'Bearer '+token} if token else {}
    with httpx.Client(base_url=os.environ.get('E2E_BASE_URL','http://127.0.0.1:9000'),headers=headers,timeout=30) as client:
        response=client.get('/health');record(response.status_code==200,'health')
        response=client.post('/commands/swe_run_agent',json={'run_id':'0'*32})
        record(response.status_code==500 and 'allow_execution=true' in response.json().get('error',''),'shell execution refuses by default')
        response=client.post('/commands/swe_run_agent',json={'run_id':'0'*32,'allow_execution':'not-a-boolean'})
        record(response.status_code==400,'typed boolean arguments')
        response=client.post('/commands/swe_prepare',json={'instance_id':'unsupported'})
        record(response.status_code==500 and 'supports only' in response.json().get('error',''),'unsupported benchmark instances refuse before checkout')
        response=client.post('/commands/swe_setup_check',json={});setup=response.json().get('result',{})
        record(response.status_code==200 and all(isinstance(x,bool) for x in setup.values()),'target settings return booleans only')
        acceptance(client)
    return 1 if FAILED else 0


if __name__=='__main__':sys.exit(main())
