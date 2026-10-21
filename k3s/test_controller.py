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


def test_safe_failure_diagnostics_never_forward_private_urls_or_arbitrary_values():
    value=c.safe_diagnostic(RuntimeError('private https://secret.invalid/resource?token=private-token diagnostic_stage=readiness; diagnostic_type=RuntimeError; native_markers=root,permission,private_token'))
    assert value=={'diagnostic_stage':'readiness','diagnostic_type':'RuntimeError','native_markers':['root','permission']}
    assert 'secret.invalid'not in str(value)and 'private-token'not in str(value)

def test_safe_failure_diagnostics_identify_only_known_ownership_errors():
    assert c.safe_diagnostic(RuntimeError('native node-state ownership differs; preserved'))=={'node_state_identity':True}

def test_native_failure_metrics_preserve_signed_exit_without_native_text():
    value=c.safe_diagnostic(RuntimeError('private text; native_exit_before_cleanup=-9; native_stdout_bytes=125; native_oom_kills=1; native_elapsed_ms=600; native_config_created=0; native_stdout_bytes=private-token'))
    assert value=={'native_exit_before_cleanup':-9,'native_stdout_bytes':125,'native_oom_kills':1,'native_elapsed_ms':600,'native_config_created':0}
    assert c.safe_diagnostic(RuntimeError('native_stdout_bytes=999999999999; native_exit_before_cleanup=https://private.invalid'))=={}
