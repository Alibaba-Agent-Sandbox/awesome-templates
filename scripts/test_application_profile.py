"""Shared canonical vectors and authored intent boundaries."""
import copy
import subprocess
import unittest
from pathlib import Path

from template_application import PROFILE_ROOT, is_managed_application, normalize_manifest, validate_manifest, project_manifest

ROOT = Path(__file__).resolve().parents[1]


class ApplicationProfileTest(unittest.TestCase):
    def test_shared_python_and_javascript_fixtures(self):
        subprocess.run(['node', str(PROFILE_ROOT / 'test.mjs')], check=True, env={**__import__('os').environ, 'PYTHON': __import__('sys').executable})
        subprocess.run([__import__('sys').executable, str(PROFILE_ROOT / 'test_contract.py')], check=True)

    def test_real_manifest_normalization_is_idempotent_and_nonmutating(self):
        import yaml
        data = yaml.safe_load((ROOT / 'python-hello/template.yaml').read_text())
        original = copy.deepcopy(data)
        normalized = normalize_manifest(data)
        self.assertEqual(normalize_manifest(normalized), normalized)
        self.assertEqual(data, original)
        self.assertEqual(validate_manifest(data, ROOT / 'python-hello'), [])
        self.assertIn('agent-sandbox-server serve', project_manifest(data, ROOT / 'python-hello')['start_cmd'])
        self.assertNotIn('startCommand', data['sandbox']['agent']['template'])

    def test_retired_application_settings_are_not_repaired(self):
        import yaml
        original = yaml.safe_load((ROOT / 'python-hello/template.yaml').read_text())
        for key in ['application', 'deployment', 'instance']:
            data = copy.deepcopy(original); data[key] = {'private': 'not-logged'}
            self.assertTrue(validate_manifest(data))
            self.assertEqual(data[key], {'private': 'not-logged'})

    def test_native_serving_classifies_and_version_only_admits_v1(self):
        import yaml
        data = yaml.safe_load((ROOT / 'python-hello/template.yaml').read_text())
        self.assertFalse(is_managed_application(data))
        for value in [5, 6, 7, None, False, '1']:
            candidate = copy.deepcopy(data); candidate['specVersion'] = value
            self.assertTrue(validate_manifest(candidate))
        data['sandbox']['agent']['template']['startCommand'] = 'python -m agent_sandbox.server.managed --port 9000'
        self.assertFalse(is_managed_application(data))
        self.assertEqual(validate_manifest(data), [])
        managed = yaml.safe_load((ROOT / 'agents-api/template.yaml').read_text())
        self.assertTrue(is_managed_application(managed))

    def test_explicit_provider_conflicts_are_rejected(self):
        import yaml
        data = yaml.safe_load((ROOT / 'python-hello/template.yaml').read_text())
        self.assertEqual(normalize_manifest(data)['sandbox']['agent']['provider'], 'alicloud-express')
        with self.assertRaises(ValueError): normalize_manifest(data, 'e2b')

    def test_no_business_or_credential_defaults_are_created(self):
        import yaml
        data = yaml.safe_load((ROOT / 'python-hello/template.yaml').read_text())
        normalized = normalize_manifest(data)
        self.assertNotIn('application', normalized)
        self.assertNotIn('instance', normalized['sandbox']['agent'])
        self.assertNotIn('environmentVariables', normalized['sandbox']['agent']['template'])
        self.assertEqual(normalized['sandbox']['agent']['template']['region'], 'cn-hangzhou')


    def test_deferred_native_fields_do_not_become_business_classification(self):
        data = {"serving": {"api": {"props": {"environmentVariables": "${vars.nativeEnv}", "customContainerConfig": None}}}}
        self.assertFalse(is_managed_application(data))
