"""Synthetic source/registration guards; these fixtures are not cloud evidence."""
import json
from pathlib import Path
import sys
from unittest.mock import patch
import pytest

sys.path.insert(0,str(Path(__file__).parent))
import ci_image
import express_e2e as h

IMAGE='registry.cn-hangzhou.aliyuncs.com/example/e2e-ci-image-'+'a'*16+':review'


def fixture(tmp_path):
    source=tmp_path/'product';source.mkdir()
    (source/'template.yaml').write_text('name: product\nversion: 1.0.0\nresources: {cpu: 2, memory: 2048}\nsmoke:\n  - command: hello\n    expect: ok\ntested_on: []\n')
    (source/'Dockerfile').write_text('FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>\nWORKDIR /home/user/app\nCOPY --chown=user:user commands.py .\nUSER user\n')
    (source/'commands.py').write_text('# immutable public runtime\n')
    proof={'schema_version':1,'verification_type':'ci-docker-archive','template':'product','template_version':'1.0.0','github_repository':'Alibaba-Agent-Sandbox/awesome-templates','source_head_commit':'b'*40,'checkout_commit':'b'*40,'workflow_run_id':'123','artifact_id':'456','archive_sha256':'c'*64,'image_config_sha256':'d'*64,'pushed_image_digest':'sha256:'+'a'*64,'server_sdk_commit':ci_image.SERVER_COMMIT,'context_sha256':ci_image.context_sha256(source),'artifact_verified':True,'image_context_verified':True,'image_non_root':True,'registry_push_verified':True,'registry_private_repo_verified':True,'registry_credentials_storage':'anonymous RAM fd','registration_reference_type':'owned tag with digest readback','tag_digest_verified_before_registration':True,'tag_digest_verified_after_runtime':False}
    path=tmp_path/'public-proof.json';path.write_text(json.dumps(proof))
    return source,proof,path


@pytest.mark.parametrize('key,value',[('artifact_verified',False),('image_non_root',False),('registry_private_repo_verified',False),('server_sdk_commit','e'*40),('template_version','9.0.0'),('github_repository','unreviewed/fork'),('pushed_image_digest','invalid'),('registry_credentials_storage','disk config'),('private_registry_password','not-public')])
def test_wrong_or_private_proof_fails_before_cloud(tmp_path,key,value):
    source,proof,path=fixture(tmp_path);proof[key]=value;path.write_text(json.dumps(proof))
    with pytest.raises(SystemExit):h.build_options([str(source),'--build','image','--image-ref',IMAGE,'--image-proof',str(path)])


def test_mutable_reference_and_changed_runtime_are_rejected(tmp_path):
    source,proof,path=fixture(tmp_path)
    with pytest.raises(ValueError):ci_image.validate_proof(source,proof,IMAGE.rsplit(':',1)[0]+':latest')
    (source/'commands.py').write_text('# modified after L1\n')
    with pytest.raises(ValueError,match='inputs differ'):ci_image.validate_proof(source,proof,IMAGE)


def test_only_tested_on_metadata_can_change_without_image_rebuild(tmp_path):
    source,proof,path=fixture(tmp_path)
    text=(source/'template.yaml').read_text().replace('tested_on: []','tested_on: [alicloud-express]');(source/'template.yaml').write_text(text)
    assert ci_image.validate_proof(source,proof,IMAGE)==proof
    (source/'template.yaml').write_text(text.replace('expect: ok','expect: different'))
    with pytest.raises(ValueError):ci_image.validate_proof(source,proof,IMAGE)


def test_real_image_entry_polls_ready_and_keeps_cli_smoke_cleanup(tmp_path,monkeypatch):
    source,proof,path=fixture(tmp_path)
    options=h.build_options([str(source),'--build','image','--image-ref',IMAGE,'--image-proof',str(path),'--sandbox-timeout','900'])
    monkeypatch.setenv('ABX_IMAGE_REGISTRY_USERNAME','synthetic-user')
    monkeypatch.setenv('ABX_IMAGE_REGISTRY_PASSWORD','synthetic-private-password')
    monkeypatch.setattr(h,'image_digest',lambda ref:proof['pushed_image_digest'])
    calls=[]
    def run(argv,timeout):
        calls.append(argv)
        if argv[1:3]==['template','info']:return h.Proc(0,'{"status":{"state":"ready"}}','')
        if '--official-api' in argv:return h.Proc(0,'[]','')
        if argv[1:3]==['template','create']:
            assert '--no-envd-inject' in argv and '--cpu' in argv and '--memory' in argv
            assert IMAGE in argv and '--registry-password=synthetic-private-password' in argv
            assert 'deploy' not in argv and '--build' not in argv
            return h.Proc(0,'{"TemplateID":"owned-image-template"}','')
        if argv[1:3]==['template','info']:return h.Proc(0,'{"status":{"state":"ready"}}','')
        if 'create' in argv:
            assert argv[-2:]==['--timeout','900']
            return h.Proc(0,'{"ID":"owned-image-sandbox"}','')
        if 'run' in argv:return h.Proc(0,'{"result":"ok"}','')
        return h.Proc(0,'','')
    with patch.object(h,'acr_push_lock',side_effect=AssertionError('no controller Docker push')):
        assert h.execute(options,runner=run,sdk=lambda *_:'ok',verify=lambda *_:True)==0
    report=json.loads(next((source/'evidence').glob('express-*.json')).read_text())
    assert report['build_mode']=='image' and report['registration_operation']=='abx template create'
    assert report['image_provenance']['tag_digest_verified_after_runtime'] is True and report['cleanup_verified'] is True
    assert any(a[1:3]==['template','info'] for a in calls) and any('kill' in a for a in calls)
    assert 'synthetic-private-password' not in json.dumps(report)


def test_failed_image_readiness_never_creates_sandbox_or_receipt(tmp_path,monkeypatch):
    source,proof,path=fixture(tmp_path)
    options=h.build_options([str(source),'--build','image','--image-ref',IMAGE,'--image-proof',str(path)])
    monkeypatch.setenv('ABX_IMAGE_REGISTRY_USERNAME','synthetic-user');monkeypatch.setenv('ABX_IMAGE_REGISTRY_PASSWORD','synthetic-private-password')
    monkeypatch.setattr(h,'image_digest',lambda ref:proof['pushed_image_digest'])
    def run(argv,timeout):
        if '--official-api' in argv:return h.Proc(0,'[]','')
        if argv[1:3]==['template','create']:return h.Proc(0,'{"TemplateID":"owned-image-template"}','')
        if 'create' in argv:pytest.fail('sandbox cannot precede image READY')
        return h.Proc(0,'','')
    with patch.object(h,'wait_for_steps_ready',return_value=False):assert h.execute(options,runner=run,sdk=lambda *_:'ok',verify=lambda *_:True)==1
    assert not (source/'evidence').exists()


def test_invalid_declared_resources_fail_before_any_artifact_or_cloud_call(tmp_path):
    import ci_image_archive
    source,proof,path=fixture(tmp_path)
    manifest=source/'template.yaml';manifest.write_text(manifest.read_text().replace('memory: 2048','memory: 1024'))
    with patch.object(ci_image_archive,'artifact_download',side_effect=AssertionError('invalid resource preflight must be read-only')):
        with pytest.raises(ValueError,match='per vCPU'):
            ci_image_archive.download_verified(123,source,tmp_path/'private')
    assert not (tmp_path/'private').exists()


def test_tag_changed_before_registration_is_rejected_without_mutation(tmp_path,monkeypatch):
    source,proof,path=fixture(tmp_path)
    options=h.build_options([str(source),'--build','image','--image-ref',IMAGE,'--image-proof',str(path)])
    monkeypatch.setenv('ABX_IMAGE_REGISTRY_USERNAME','synthetic-user');monkeypatch.setenv('ABX_IMAGE_REGISTRY_PASSWORD','synthetic-password')
    monkeypatch.setattr(h,'image_digest',lambda ref:'sha256:'+'0'*64)
    def run(argv,timeout):
        if '--official-api' in argv:return h.Proc(0,'[]','')
        pytest.fail('no cloud mutation before digest match')
    assert h.execute(options,runner=run,sdk=lambda *_:'ok',verify=lambda *_:True)==1
    assert not (source/'evidence').exists()


def test_changed_tag_after_runtime_cannot_publish_even_when_cleanup_succeeds(tmp_path,monkeypatch):
    source,proof,path=fixture(tmp_path)
    options=h.build_options([str(source),'--build','image','--image-ref',IMAGE,'--image-proof',str(path)])
    monkeypatch.setenv('ABX_IMAGE_REGISTRY_USERNAME','synthetic-user');monkeypatch.setenv('ABX_IMAGE_REGISTRY_PASSWORD','synthetic-password')
    digests=iter([proof['pushed_image_digest'],'sha256:'+'0'*64])
    monkeypatch.setattr(h,'image_digest',lambda ref:next(digests))
    def run(argv,timeout):
        if argv[1:3]==['template','info']:return h.Proc(0,'{"status":{"state":"ready"}}','')
        if '--official-api' in argv:return h.Proc(0,'[]','')
        if argv[1:3]==['template','create']:return h.Proc(0,'{"TemplateID":"owned-template"}','')
        if 'create' in argv:return h.Proc(0,'{"ID":"owned-sandbox"}','')
        if 'run' in argv:return h.Proc(0,'{"result":"ok"}','')
        return h.Proc(0,'','')
    assert h.execute(options,runner=run,sdk=lambda *_:'ok',verify=lambda *_:True)==1
    assert not (source/'evidence').exists()
