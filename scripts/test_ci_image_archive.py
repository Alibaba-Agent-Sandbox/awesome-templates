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
