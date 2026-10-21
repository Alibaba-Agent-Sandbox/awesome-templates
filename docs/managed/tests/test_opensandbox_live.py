"""Local tests only cover receipt diagnostics; native execution runs in hosted Docker."""
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('managed_opensandbox_live',Path(__file__).with_name('opensandbox_live.py'))
live=importlib.util.module_from_spec(spec);spec.loader.exec_module(live)

def test_unexpected_error_diagnostics_do_not_copy_ids_credentials_or_locations():
    text=live.safe_error(RuntimeError('failed native endpoint https://localhost:8080/v1/sandboxes/1234567890abcdef with fixed-synthetic-opensandbox-key at /home/runner/private; id abcdef12-3456-7890-abcd-1234567890ab'))
    assert 'failed native endpoint'in text
    assert all(value not in text for value in ['localhost','8080','1234567890abcdef','fixed-synthetic','/home/runner','abcdef12-3456'])
    assert len(live.safe_error(RuntimeError('x'*1000)))==400
