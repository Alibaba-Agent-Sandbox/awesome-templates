"""Small authored archives test filesystem integrity; no vendor program executes."""
import hashlib,importlib.util,io,tarfile
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('devin_install_fixture',Path(__file__).with_name('install_runtime.py'))
i=importlib.util.module_from_spec(spec);spec.loader.exec_module(i)

def archive(tmp_path,name='bin/devin',kind=None):
    path=tmp_path/'fixture.tar.gz';data=b'FIXED_AUTHORED_DATA'
    with tarfile.open(path,'w:gz')as output:
        item=tarfile.TarInfo(name);item.size=len(data)
        if kind:item.type=kind;item.size=0;item.linkname='../../outside'
        output.addfile(item,None if kind else io.BytesIO(data))
    metadata={'files':[{'path':'bin/devin','size':len(data),'sha256':hashlib.sha256(data).hexdigest(),'executable':False}]}
    return path,metadata

def test_fixed_archive_preserved_and_changed_file_rejected(tmp_path):
    path,metadata=archive(tmp_path);destination=tmp_path/'target';destination.mkdir()
    root=i.extract(path,destination,metadata);assert(root/'bin/devin').read_bytes()==b'FIXED_AUTHORED_DATA'
    (root/'bin/devin').chmod(0o600);(root/'bin/devin').write_bytes(b'CHANGED_AUTHORED_DA')
    with pytest.raises(ValueError):i.verify_tree(root,metadata)

@pytest.mark.parametrize('name,kind',[('bin/../../outside',None),('/bin/devin-agent',None),('bin/devin',tarfile.SYMTYPE),('bin/devin',tarfile.LNKTYPE)])
def test_path_or_link_escape_preserves_foreign_file(tmp_path,name,kind):
    foreign=tmp_path/'outside';foreign.write_text('PRESERVE')
    path,metadata=archive(tmp_path,name,kind);destination=tmp_path/'target';destination.mkdir()
    with pytest.raises(ValueError):i.extract(path,destination,metadata)
    assert foreign.read_text()=='PRESERVE'
