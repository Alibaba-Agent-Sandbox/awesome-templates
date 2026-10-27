"""Synthetic source/registration guards; these fixtures are not cloud evidence."""
import json
from pathlib import Path
import sys
from unittest.mock import patch
import pytest

sys.path.insert(0,str(Path(__file__).parent))
import ci_image

IMAGE='registry.cn-hangzhou.aliyuncs.com/example/e2e-ci-image-'+'a'*16+':review'


def fixture(tmp_path):
    source=tmp_path/'product';source.mkdir()
    (source/'template.yaml').write_text('name: product\nversion: 1.0.0\nresources: {cpu: 2, memory: 2048}\nsmoke:\n  - command: hello\n    expect: ok\ntested_on: []\n')
    (source/'Dockerfile').write_text('FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>\nRUN pip install agent-sandbox-server==0.4.0a6\nWORKDIR /home/user/app\nCOPY --chown=user:user commands.py .\nUSER user\n')
    (source/'commands.py').write_text('# immutable public runtime\n')
    proof={'schema_version':1,'verification_type':'ci-docker-archive','template':'product','template_version':'1.0.0','github_repository':'Alibaba-Agent-Sandbox/awesome-templates','source_head_commit':'b'*40,'checkout_commit':'b'*40,'workflow_run_id':'123','artifact_id':'456','archive_sha256':'c'*64,'image_config_sha256':'d'*64,'pushed_image_digest':'sha256:'+'a'*64,'server_package_version':'0.4.0a6','context_sha256':ci_image.context_sha256(source),'artifact_verified':True,'image_context_verified':True,'image_non_root':True,'registry_push_verified':True,'registry_private_repo_verified':True,'registry_credentials_storage':'anonymous RAM fd','registration_reference_type':'owned tag with digest readback','tag_digest_verified_before_registration':True,'tag_digest_verified_after_runtime':False}
    path=tmp_path/'public-proof.json';path.write_text(json.dumps(proof))
    return source,proof,path


@pytest.mark.parametrize('key,value',[('artifact_verified',False),('image_non_root',False),('registry_private_repo_verified',False),('server_package_version','e'*40),('template_version','9.0.0'),('github_repository','unreviewed/fork'),('pushed_image_digest','invalid'),('registry_credentials_storage','disk config'),('private_registry_password','not-public')])
def test_wrong_or_private_proof_fails_before_cloud(tmp_path,key,value):
    source,proof,path=fixture(tmp_path);proof[key]=value;path.write_text(json.dumps(proof))
    with pytest.raises(ValueError):ci_image.validate_proof(source,proof,IMAGE)


def test_mutable_reference_and_changed_runtime_are_rejected(tmp_path):
    source,proof,path=fixture(tmp_path)
    with pytest.raises(ValueError):ci_image.validate_proof(source,proof,IMAGE.rsplit(':',1)[0]+':latest')
    (source/'commands.py').write_text('# modified after L1\n')
    with pytest.raises(ValueError,match='inputs differ'):ci_image.validate_proof(source,proof,IMAGE)


def test_any_manifest_change_invalidates_image_identity(tmp_path):
    source,proof,path=fixture(tmp_path)
    text=(source/'template.yaml').read_text().replace('tested_on: []','tested_on: [alicloud-express]');(source/'template.yaml').write_text(text)
    with pytest.raises(ValueError):ci_image.validate_proof(source,proof,IMAGE)
    (source/'template.yaml').write_text(text.replace('expect: ok','expect: different'))
    with pytest.raises(ValueError):ci_image.validate_proof(source,proof,IMAGE)






def test_invalid_declared_resources_fail_before_any_artifact_or_cloud_call(tmp_path):
    import ci_image_archive
    source,proof,path=fixture(tmp_path)
    manifest=source/'template.yaml';manifest.write_text(manifest.read_text().replace('memory: 2048','memory: 1024'))
    with patch.object(ci_image_archive,'artifact_download',side_effect=AssertionError('invalid resource preflight must be read-only')):
        with pytest.raises(ValueError,match='per vCPU'):
            ci_image_archive.download_verified(123,source,tmp_path/'private')
    assert not (tmp_path/'private').exists()






def test_proof_requires_the_declared_public_server_package(tmp_path):
    source,proof,_=fixture(tmp_path)
    path=source/'Dockerfile'
    path.write_text(path.read_text().replace('0.4.0a6','0.4.0a2'))
    proof['context_sha256']=ci_image.context_sha256(source)
    with pytest.raises(ValueError,match='server package'):
        ci_image.validate_proof(source,proof,IMAGE)
    proof['server_package_version']='0.4.0a2'
    assert ci_image.validate_proof(source,proof,IMAGE)==proof


@pytest.mark.parametrize('pin',['agent-sandbox-server', 'agent-sandbox-server>=0.4.0a6', 'agent-sandbox-server==0.4.0a6 agent-sandbox-server==0.4.0a2'])
def test_missing_or_conflicting_public_server_pins_are_rejected(tmp_path,pin):
    source,_,_=fixture(tmp_path)
    (source/'Dockerfile').write_text('RUN pip install '+pin+'\n')
    with pytest.raises(ValueError,match='one exact public'):
        ci_image.server_version(source)


def test_private_archive_staging_keeps_registry_auth_on_native_temp_filesystem(tmp_path, monkeypatch):
    import subprocess
    import tempfile
    import ci_image_archive as images
    import run_ci_image_e2e as runner
    repo = tmp_path / 'repo'
    repo.mkdir()
    source, _, _ = fixture(repo)
    private = tmp_path / 'private-archives'
    native_temp = Path(tempfile.gettempdir()).resolve()

    def download(artifact_id, current_source, stage):
        assert stage.parent.parent == private
        with images.ram_registry_auth('synthetic-user', 'synthetic-password') as (env, fds):
            auth = Path(env['DOCKER_CONFIG'])
            assert auth.parent == native_temp and not auth.is_relative_to(private)
            result = subprocess.run([sys.executable, '-c',
                "import os,json,pathlib;p=pathlib.Path(os.environ['DOCKER_CONFIG'])/'config.json';assert p.is_symlink();assert json.loads(p.read_text())['auths']"],
                env=env, pass_fds=fds, capture_output=True, text=True)
            assert result.returncode == 0
        assert not auth.exists()
        raise ValueError('synthetic archive refusal before any cloud operation')

    monkeypatch.setattr(images, 'download_verified', download)
    monkeypatch.setattr(runner, 'check_image_cli', lambda: None)
    assert runner.run(source, 123, '/unused/crane', http=False, private_root=private) == 1
    assert Path(tempfile.gettempdir()).resolve() == native_temp
    receipt = json.loads(next((source / 'evidence').glob('image-attempt-*.json')).read_text())
    assert receipt['passed'] is False and receipt['runtime_attempted'] is False


def test_archive_staging_inside_checkout_is_rejected_before_any_cloud_call(tmp_path):
    import run_ci_image_e2e as runner
    source, _, _ = fixture(tmp_path)
    with pytest.raises(ValueError, match='outside the source checkout'):
        runner.run(source, 123, '/unused/crane', http=False, private_root=source)


def test_controller_preflight_checks_nested_local_protocol_helpers(tmp_path):
    import run_ci_image_e2e as runner
    (tmp_path / 'e2e_test.py').write_text('from peer_client import Client\n')
    (tmp_path / 'peer_client.py').write_text('import abx_missing_controller_dependency\nclass Client: pass\n')
    assert runner.controller_missing_imports(tmp_path) == ['abx_missing_controller_dependency']


def test_missing_image_cli_contract_blocks_before_archive_or_registry_calls(tmp_path, monkeypatch):
    import ci_image_archive as images
    import run_ci_image_e2e as runner
    repo = tmp_path / 'repo'
    repo.mkdir()
    source, _, _ = fixture(repo)
    monkeypatch.setattr(runner.CLI, 'run', lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError('native CLI unavailable')))
    monkeypatch.setattr(images, 'download_verified', lambda *args: pytest.fail('CLI preflight must precede downloads/cloud operations'))
    assert runner.run(source, 123, '/unused/crane', http=False, private_root=tmp_path / 'private') == 1
    receipt = json.loads(next((source / 'evidence').glob('image-attempt-*.json')).read_text())
    assert receipt['runtime_attempted'] is False and receipt['passed'] is False


def test_server_version_comes_from_the_public_package_declaration(tmp_path):
    source, _, _ = fixture(tmp_path)
    (source / 'Dockerfile').write_text('RUN pip install agent-sandbox-server==0.4.0a6\n')
    assert ci_image.server_version(source) == '0.4.0a6'
