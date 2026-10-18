"""Reject corrupted public binaries before extraction or execution."""
import importlib.util
from pathlib import Path
import pytest

SPEC=importlib.util.spec_from_file_location('pi_pinned_installer',Path(__file__).with_name('install_tools.py'))
installer=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(installer)


def test_archive_checksum_failure_never_extracts_or_executes(monkeypatch,tmp_path):
    monkeypatch.setattr(installer.platform,'machine',lambda:'x86_64')
    monkeypatch.setattr(installer.urllib.request,'urlretrieve',lambda url,path:path.write_bytes(b'synthetic corrupted archive'))
    monkeypatch.setattr(installer.tarfile,'open',lambda *a,**k:pytest.fail('unverified archive must not be extracted'))
    monkeypatch.setattr(installer.subprocess,'check_output',lambda *a,**k:pytest.fail('unverified binary must not run'))
    with pytest.raises(RuntimeError,match='SHA256 mismatch'):installer.install(tmp_path/'tools',tmp_path/'bin')
    assert list((tmp_path/'bin').iterdir())==[]


def test_unknown_architecture_does_not_download(monkeypatch,tmp_path):
    monkeypatch.setattr(installer.platform,'machine',lambda:'unsupported')
    monkeypatch.setattr(installer.urllib.request,'urlretrieve',lambda *a:pytest.fail('unknown architecture must not download'))
    with pytest.raises(RuntimeError,match='x86_64/aarch64'):installer.install(tmp_path/'tools',tmp_path/'bin')
