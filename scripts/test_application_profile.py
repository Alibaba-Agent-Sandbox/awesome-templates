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
        data = yaml.safe_load((ROOT / 'agents-api/template.yaml').read_text())
        original = copy.deepcopy(data)
        normalized = normalize_manifest(data)
        self.assertEqual(normalize_manifest(normalized), normalized)
        self.assertEqual(data, original)
        self.assertEqual(validate_manifest(data, ROOT / 'agents-api'), [])
        self.assertEqual(project_manifest(data, ROOT / 'agents-api')['application']['sessions']['maxLifetimeSeconds'], data['sandbox']['instance']['timeout'])

    def test_explicit_conflicts_are_not_repaired(self):
        import yaml
        original = yaml.safe_load((ROOT / 'agents-api/template.yaml').read_text())
        for section, field, value in [('sessions', 'maxConcurrentTurnsPerSession', 2), ('sessions', 'maxLifetimeSeconds', 3600), ('state', 'profile', 'ephemeral')]:
            data = copy.deepcopy(original)
            data['application'].setdefault(section, {})[field] = value
            self.assertTrue(validate_manifest(data))
            self.assertEqual(data['application'][section][field], value)

    def test_business_type_classifies_and_version_only_admits_v1(self):
        import yaml
        data = yaml.safe_load((ROOT / 'agents-api/template.yaml').read_text())
        self.assertTrue(is_managed_application(data))
        for value in [5, 6, 7, None, False, '1']:
            candidate = copy.deepcopy(data); candidate['specVersion'] = value
            self.assertTrue(validate_manifest(candidate))
        data['application']['type'] = 'other'
        self.assertFalse(is_managed_application(data))
        self.assertTrue(validate_manifest(data))

    def test_unbound_source_and_explicit_provider_conflicts(self):
        import yaml
        data = yaml.safe_load((ROOT / 'python-hello/template.yaml').read_text())
        self.assertNotIn('provider', normalize_manifest(data)['sandbox'])
        self.assertEqual(normalize_manifest(data, 'e2b')['sandbox']['provider'], 'e2b')
        data['sandbox']['provider'] = 'e2b'
        with self.assertRaises(ValueError):
            normalize_manifest(data, 'opensandbox')

    def test_binding_defaults_preserve_security_boundaries(self):
        import yaml
        data = yaml.safe_load((ROOT / 'agents-api/template.yaml').read_text())
        normalized = normalize_manifest(data)
        self.assertTrue(normalized['application']['bindings']['clientAuth']['generate'])
        self.assertTrue(normalized['application']['bindings']['internalAuth']['generate'])
        for patch in [{'targets': ['gateway']}, {'allowedEnv': ['ALIBABA_CLOUD_ACCESS_KEY_SECRET']}, {'resolverRole': 'gateway'}]:
            invalid = copy.deepcopy(data); invalid['application']['bindings']['model'].update(patch)
            self.assertTrue(validate_manifest(invalid))
        for key in ['model', 'sandboxAccess']:
            invalid = copy.deepcopy(data); del invalid['application']['bindings'][key]
            self.assertTrue(validate_manifest(invalid))
