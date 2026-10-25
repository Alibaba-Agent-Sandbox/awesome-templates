"""Archive/provenance and RAM-only credential regressions; no real cloud calls."""
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tarfile
from unittest.mock import patch
import pytest
sys.path.insert(0,str(Path(__file__).parent))
import ci_image_archive as images
import run_ci_image_e2e as review


def tar_bytes(entries):
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w') as archive:
        for name,content,kind in entries:
            entry=tarfile.TarInfo(name);entry.type=kind;entry.size=len(content) if kind==tarfile.REGTYPE else 0
            archive.addfile(entry,io.BytesIO(content) if entry.size else None)
    return stream.getvalue()


def image_file(tmp_path,layers,user='user'):
    config=json.dumps({'os':'linux','architecture':'amd64','config':{'User':user,'WorkingDir':'/home/user/app'}}).encode()
    filename=hashlib.sha256(config).hexdigest()+'.json';names=[str(i)+'/layer.tar' for i in range(len(layers))]
    manifest=json.dumps([{'Config':filename,'Layers':names}]).encode()
    image=tar_bytes([(filename,config,tarfile.REGTYPE),('manifest.json',manifest,tarfile.REGTYPE)]+[(name,tar_bytes(content),tarfile.REGTYPE) for name,content in zip(names,layers)])
    path=tmp_path/'image.tar';path.write_bytes(image);return path


def test_final_actual_layer_bytes_and_whiteout(tmp_path):
    command=('home/user/app/commands.py',b'old',tarfile.REGTYPE)
    latest=('home/user/app/commands.py',b'actual',tarfile.REGTYPE)
    path=image_file(tmp_path,[[command],[latest]])
    assert images.archive_runtime(path)[1]==b'actual'
    path=image_file(tmp_path,[[command],[('home/user/app/.wh.commands.py',b'',tarfile.REGTYPE)]])
    with pytest.raises(ValueError,match='hides or deletes'):images.archive_runtime(path)


@pytest.mark.parametrize('name,kind',[('home/user/app',tarfile.SYMTYPE),('home/user/app/.wh..wh..opq',tarfile.REGTYPE)])
def test_later_ancestor_replacement_does_not_fall_back(tmp_path,name,kind):
    path=image_file(tmp_path,[[('home/user/app/commands.py',b'old',tarfile.REGTYPE)],[(name,b'',kind)]])
    with pytest.raises(ValueError):images.archive_runtime(path)


def test_root_runtime_and_nonregular_commands_are_rejected(tmp_path):
    path=image_file(tmp_path,[[('home/user/app/commands.py',b'old',tarfile.REGTYPE)]],user='root')
    with pytest.raises(ValueError):images.archive_runtime(path)
    path=image_file(tmp_path,[[('home/user/app/commands.py',b'',tarfile.SYMTYPE)]])
    with pytest.raises(ValueError):images.archive_runtime(path)


def test_credentials_are_only_in_inherited_anonymous_ram():
    with images.ram_registry_auth('synthetic-user','synthetic-password') as (env,fds):
        folder=Path(env['DOCKER_CONFIG']);config=folder/'config.json'
        assert config.is_symlink() and list(folder.iterdir())==[config]
        result=subprocess.check_output([sys.executable,'-c','import pathlib,sys;sys.stdout.buffer.write(pathlib.Path(sys.argv[1]).read_bytes())',str(config)],pass_fds=fds)
        assert 'auths' in json.loads(result)
        assert stat.S_IMODE(folder.stat().st_mode)==0o700
    assert not folder.exists()
    with pytest.raises(OSError):os.fstat(fds[0])


def test_atomic_private_journal_preserves_existing_parent_permissions(tmp_path):
    tmp_path.chmod(0o755);path=tmp_path/'intent.json'
    images.save_private(path,{'owned':True});images.save_private(path,{'owned':False})
    assert stat.S_IMODE(tmp_path.stat().st_mode)==0o755
    assert stat.S_IMODE(path.stat().st_mode)==0o600
    assert json.loads(path.read_text())=={'owned':False}
    assert list(tmp_path.iterdir())==[path]


def test_cleanup_refuses_other_namespace_or_tags(tmp_path,monkeypatch):
    monkeypatch.setenv('ACR_NAMESPACE','owned')
    journal={'namespace':'other','repository':'e2e-ci-image-'+'a'*16,'preflight_absent':True,'push_attempted':True,'owned_tags':['source-guard','review']}
    with patch.object(images,'acr_request',side_effect=AssertionError('no network')):
        with pytest.raises(ValueError):images.owned_registry_cleanup(journal,tmp_path/'journal')


def test_failed_registry_cleanup_never_publishes_provider_pass(tmp_path):
    source=tmp_path/'source';source.mkdir()
    with pytest.raises(ValueError):review.publish(source,{'passed':True},{'passed':True,'registry_cleanup_verified':False})
    assert not (source/'evidence').exists()


def test_missing_controller_dependency_is_found_before_artifact_or_cloud(tmp_path):
    source=tmp_path/'source';source.mkdir();(source/'e2e_test.py').write_text('import synthetic_missing_controller_dependency\n')
    with patch.object(images,'download_verified',side_effect=AssertionError('no artifact operation for an unusable controller')):
        assert review.run(source,123,'unused-crane')==1
    report=json.loads(next((source/'evidence').glob('image-attempt-*.json')).read_text())
    assert report['missing_controller_modules']==['synthetic_missing_controller_dependency']
    assert report['passed'] is False


def public_export():
    return {'origin': 'public-template-launch', 'runtime_server_version': '0.3.0',
        'public_source_commit': 'a'*40, 'source_head_commit': 'a'*40, 'source_snapshot_digest': 'c'*64,
        'installed_packages': {'distribution': 'published',
            'cli': {'version': '0.5.1', 'registry': 'https://registry.npmjs.org'},
            'python_client': {'version': '0.4.0a1', 'registry': 'https://pypi.org/simple'},
            'python_server': {'version': '0.4.0a1', 'registry': 'https://pypi.org/simple'}}}


def test_public_export_requires_matching_workflow_and_observed_runtime():
    data=public_export();workflow={'path': '.github/workflows/public-template-launch.yml'}
    images.validate_archive_origin(data, workflow)
    with pytest.raises(ValueError, match='workflow origin'):
        images.validate_archive_origin(data, {'path': '.github/workflows/image-build.yml'})
    data.pop('runtime_server_version')
    with pytest.raises(ValueError, match='observed runtime'):
        images.validate_archive_origin(data, workflow)


@pytest.mark.parametrize('field', ['cli', 'python_client', 'python_server'])
def test_public_export_rejects_source_or_unofficial_package_provenance(field):
    workflow={'path': '.github/workflows/public-template-launch.yml'}
    data=public_export();data['installed_packages'][field]['registry']='https://unreviewed.invalid'
    with pytest.raises(ValueError, match='official package'):
        images.validate_archive_origin(data,workflow)
    data=public_export();data['installed_packages']['distribution']='source'
    with pytest.raises(ValueError, match='published-package'):
        images.validate_archive_origin(data,workflow)


def test_historical_export_is_not_relabelled_public():
    images.validate_archive_origin({'server_sdk_commit': 'a'*40}, {'path': '.github/workflows/image-build.yml'})


def test_public_template_revision_is_distinct_from_verifier_revision():
    public='a'*40;verifier='b'*40
    metadata={'origin':'public-template-launch','source_head_commit':public,'checkout_commit':public,
        'verifier_commit':verifier,'workflow_run_id':'123'}
    workflow={'event':'workflow_dispatch','head_sha':verifier,'id':123}
    artifact={'workflow_run':{'head_sha':verifier},'name':'image-example-'+verifier}
    images.validate_archive_revisions(metadata,workflow,artifact,'example')
    metadata.pop('verifier_commit')
    with pytest.raises(ValueError,match='distinct verifier'):
        images.validate_archive_revisions(metadata,workflow,artifact,'example')
    metadata['verifier_commit']=public
    with pytest.raises(ValueError,match='exact-source'):
        images.validate_archive_revisions(metadata,workflow,artifact,'example')


def test_public_artifact_name_must_identify_actual_verifier():
    public='a'*40;verifier='b'*40
    metadata={'origin':'public-template-launch','source_head_commit':public,'checkout_commit':public,
        'verifier_commit':verifier,'workflow_run_id':'123'}
    workflow={'event':'workflow_dispatch','head_sha':verifier,'id':123}
    artifact={'workflow_run':{'head_sha':verifier},'name':'image-example-'+public}
    with pytest.raises(ValueError,match='CI identity'):
        images.validate_archive_revisions(metadata,workflow,artifact,'example')


def test_public_export_refuses_mixed_public_and_verifier_source_labels():
    data=public_export();data['public_source_commit']='b'*40
    with pytest.raises(ValueError,match='pinned public input'):
        images.validate_archive_origin(data,{'path':'.github/workflows/public-template-launch.yml'})


def test_prepared_image_uses_shared_startup_contract_and_current_services(tmp_path):
    import yaml
    source=tmp_path/'example';source.mkdir()
    manifest={'spec_version':5,'name':'example','version':'1.0.0','start_cmd':'python commands.py',
        'ready_cmd':'python check.py','env':{'ABX_SERVER_TOKEN':'','OTHER':'fixed'},
        'ports':[9000,9001],'provides':{'app':{'protocol':'agent-sandbox-server','version':2,
        'port':9000,'operations':['commands.run']}},'smoke':[{'command':'hello'}]}
    (source/'template.yaml').write_text(yaml.safe_dump(manifest))
    actual=review.prepared_launch_manifest(source,'owned-template')
    assert actual==dict(manifest,provider='alicloud-express',template_id='owned-template')
    assert yaml.safe_load((source/'template.yaml').read_text())==manifest


def test_native_readiness_consumes_structured_json_and_rejects_legacy_python_strings():
    from types import SimpleNamespace
    calls=[]
    cli=SimpleNamespace(run=lambda args,**kwargs: calls.append((args,kwargs)) or {'status':{'state':'ready'}})
    review.wait_ready(cli,'owned-template',timeout=1)
    assert calls==[(['template','info','owned-template'],{'native':True})]
    cli.run=lambda *args,**kwargs:{'status':"{'state': 'ready'}"}
    with pytest.raises(AssertionError):review.wait_ready(cli,'owned-template',timeout=1)


def test_native_inventory_matches_only_exact_owned_name():
    from types import SimpleNamespace
    cli=SimpleNamespace(run=lambda *args,**kwargs:[{'Name':'owned','TemplateID':'correct'},
        {'Name':'owned-extra','TemplateID':'foreign'},{'Name':'other','TemplateID':'another'}])
    assert review.exact_templates(cli,'owned')==['correct']
