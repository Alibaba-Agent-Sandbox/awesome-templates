"""Authored path/process regressions; no original QM/model code on operator."""
import importlib.util
from pathlib import Path
import pytest


def load(name):
    spec=importlib.util.spec_from_file_location('qm_authored_'+name,Path(__file__).with_name(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('action',['read','write','remove','list'])
def test_path_traversal_and_symlink_escape_leave_caller_file_unchanged(tmp_path,action):
    root=tmp_path/'project';root.mkdir();outside=tmp_path/'caller.txt';outside.write_text('preserve')
    (root/'escape').symlink_to(outside)
    helper=load('sdk_path')
    for path in ['../caller.txt','escape']:
        with pytest.raises(ValueError):helper.operate(action,str(root),path)
    assert outside.read_text()=='preserve'


def test_directory_bounds_and_private_parent_creation(tmp_path):
    helper=load('sdk_path');target=helper.operate('write',str(tmp_path),'nested/target.txt')
    assert target==str(tmp_path/'nested/target.txt')
    assert (tmp_path/'nested').stat().st_mode&0o777==0o700
    for index in range(1025):(tmp_path/('entry'+str(index))).touch()
    with pytest.raises(ValueError):helper.operate('list',str(tmp_path),'')


def test_real_authored_tool_subprocess_clears_operator_keys_and_preserves_exit_124(tmp_path,monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','synthetic-operator-secret')
    monkeypatch.setenv('ABX_SERVER_TOKEN','synthetic-server-secret')
    command="python3 -I -c 'import os; assert not os.environ.get(\"OPENAI_API_KEY\"); assert not os.environ.get(\"ABX_SERVER_TOKEN\"); print(\"AUTHORED_TOOL_OK\")'; exit 124"
    value=load('sdk_exec').run(str(tmp_path),command,10)
    assert value=={'stdout':'AUTHORED_TOOL_OK\n','stderr':'','code':124,'timedOut':False}


def test_real_authored_tool_timeout_cleans_owned_descendants(tmp_path):
    value=load('sdk_exec').run(str(tmp_path),'sleep 10',1)
    assert value['code']==124 and value['timedOut']is True


@pytest.mark.parametrize('kind',['traversal','symlink','hardlink'])
def test_installer_rejects_archive_escape_before_touching_caller_file(tmp_path,kind):
    import io,tarfile
    archive=tmp_path/'fixture.tar.gz';outside=tmp_path/'caller.txt';outside.write_text('preserve')
    with tarfile.open(archive,'w:gz')as bundle:
        root=tarfile.TarInfo('bundle');root.type=tarfile.DIRTYPE;bundle.addfile(root)
        item=tarfile.TarInfo('bundle/'+('../caller.txt'if kind=='traversal'else'link'))
        if kind=='symlink':item.type=tarfile.SYMTYPE;item.linkname='../../caller.txt';bundle.addfile(item)
        elif kind=='hardlink':item.type=tarfile.LNKTYPE;item.linkname='bundle/caller.txt';bundle.addfile(item)
        else:item.size=7;bundle.addfile(item,io.BytesIO(b'changed'))
    with pytest.raises(ValueError):load('install_runtime').extract(archive,tmp_path/'destination')
    assert outside.read_text()=='preserve'


def test_installer_retains_original_safe_internal_symlink_and_notice(tmp_path):
    import io,tarfile
    archive=tmp_path/'fixture.tar.gz'
    with tarfile.open(archive,'w:gz')as bundle:
        root=tarfile.TarInfo('bundle');root.type=tarfile.DIRTYPE;bundle.addfile(root)
        item=tarfile.TarInfo('bundle/LICENSE');item.size=16;bundle.addfile(item,io.BytesIO(b'original notice\n'))
        link=tarfile.TarInfo('bundle/NOTICE');link.type=tarfile.SYMTYPE;link.linkname='LICENSE';bundle.addfile(link)
    target=tmp_path/'destination';load('install_runtime').extract(archive,target)
    assert (target/'NOTICE').is_symlink()and(target/'NOTICE').read_text()=='original notice\n'
