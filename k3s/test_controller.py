"""Completion evidence rejects stale native IDs and operator control-plane runs."""
import importlib.util
from pathlib import Path
from unittest.mock import Mock
import pytest
spec=importlib.util.spec_from_file_location('k3s_controller_unit',Path(__file__).with_name('e2e_test.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
@pytest.mark.parametrize('base',['http://localhost:9000','http://127.0.0.1:9000','http://[::1]:9000','http://[::ffff:127.0.0.1]:9000','http://0.0.0.0:9000'])
def test_original_server_never_runs_on_a_local_target(base,monkeypatch):
    monkeypatch.setenv('E2E_REMOTE_SANDBOX','1');c.RESULTS.clear();client=Mock();c.native(client,base);assert c.RESULTS==[False];client.post.assert_not_called()
def test_version_or_valid_marker_without_exact_original_identity_is_not_completion():
    assert not c.identity({'valid':True,'native_version':'v1.37.1+k3s1'})
    assert not c.identity({'valid':'true','mode':'original-k3s-agentless-validation','native_version':'v1.37.1+k3s1','native_sha256':c.SHA})
    assert not c.cleaned({'api_server_stopped':True})
