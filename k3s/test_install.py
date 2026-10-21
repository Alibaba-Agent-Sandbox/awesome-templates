"""Authored data only: original binary size/hash checks never execute it."""
import hashlib,importlib.util
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('k3s_install_unit',Path(__file__).with_name('install_runtime.py'))
i=importlib.util.module_from_spec(spec);spec.loader.exec_module(i)
def test_original_size_hash_and_symlink_controls(tmp_path,monkeypatch):
    data=b'FIXED_AUTHORED_BINARY_DATA';path=tmp_path/'binary';path.write_bytes(data)
    monkeypatch.setitem(i.PIN,'size',len(data));monkeypatch.setitem(i.PIN,'sha256',hashlib.sha256(data).hexdigest());i.verify(path)
    link=tmp_path/'link';link.symlink_to(path)
    with pytest.raises(ValueError):i.verify(link)
    path.write_bytes(b'X'*len(data))
    with pytest.raises(ValueError):i.verify(path)
