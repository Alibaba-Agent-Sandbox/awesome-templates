import importlib.util
import json
from pathlib import Path
import httpx
import pytest

spec=importlib.util.spec_from_file_location('swe_e2e',Path(__file__).with_name('e2e_test.py'))
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
manifest=json.loads(Path(__file__).with_name('instance.json').read_text())


def report():
    return {'resolved_slice':True,'official_benchmark_score':False,'passed':60,'failed':0,'errors':0,'skipped':0,
        'fail_to_pass':dict.fromkeys(manifest['fail_to_pass'],'passed'),'pass_to_pass':dict.fromkeys(manifest['pass_to_pass'],'passed')}


def test_actual_test_identity_sets_required():
    value=report();assert e.valid_evaluation(value)
    value['pass_to_pass'].pop(next(iter(value['pass_to_pass'])));assert not e.valid_evaluation(value)


@pytest.mark.parametrize('changes',[{'passed':1},{'skipped':1},{'errors':1},{'failed':1},{'official_benchmark_score':True},{'resolved_slice':False},{'fail_to_pass':{}}])
def test_false_green_scores_refused(changes):
    assert not e.valid_evaluation(report()|changes)


def test_required_model_missing_target_cannot_skip(monkeypatch):
    monkeypatch.setenv('E2E_REQUIRE_LLM','1');monkeypatch.setenv('E2E_RUN_LLM','1');monkeypatch.setenv('SWE_API_KEY','host-only-synthetic')
    requests=[]
    def respond(request):
        requests.append(request.url.path);return httpx.Response(200,json={'result':{'api_key_set':False,'base_url_set':False,'model_set':False,'runtime_available':True}})
    e.FAILED=0
    with httpx.Client(base_url='http://owned.test',transport=httpx.MockTransport(respond)) as client:e.acceptance(client)
    assert e.FAILED==1 and requests==['/commands/swe_setup_check']


def test_required_model_explicit_off_cannot_skip(monkeypatch):
    monkeypatch.setenv('E2E_REQUIRE_LLM','1');monkeypatch.setenv('E2E_RUN_LLM','0')
    e.FAILED=0
    with httpx.Client(base_url='http://owned.test',transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'result':{}}))) as client:e.acceptance(client)
    assert e.FAILED==1
