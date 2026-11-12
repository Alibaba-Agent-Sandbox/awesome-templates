"""Observable v1 admission, source containment and source-only validation."""
from __future__ import annotations
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import check_template
import yaml
from template_application import SCHEMA_PATH, validate_manifest, engineering_checks

ROOT = Path(__file__).resolve().parents[1]


class ApplicationContractTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(); self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.template = self.root / '_skeleton'; shutil.copytree(ROOT / '_skeleton', self.template)
        self.data = yaml.safe_load((self.template / 'template.yaml').read_text())

    def check(self, data=None):
        return validate_manifest(self.data if data is None else data, self.template)

    def test_schema_is_valid(self):
        from jsonschema import Draft202012Validator
        Draft202012Validator.check_schema(json.loads(SCHEMA_PATH.read_text()))

    def test_documented_examples_match_machine_contract(self):
        for source in sorted((ROOT / 'docs/examples').glob('*/template.yaml')):
            with self.subTest(source=source):
                self.assertEqual(validate_manifest(yaml.safe_load(source.read_text()), source.parent), [])

    def test_current_default_without_registry_is_valid(self):
        self.assertFalse((self.template / 'registry.yaml').exists())
        self.assertEqual(self.check(), [])
        self.assertEqual(check_template.check_directory(self.template), [])

    def test_existing_engineering_expectations_remain_separate_from_resources(self):
        catalog = yaml.safe_load((ROOT / 'awesome-templates.yaml').read_text())
        for row in catalog['templates']:
            data = yaml.safe_load((ROOT / row['path'] / 'template.yaml').read_text())
            with self.subTest(template=row['name']):
                self.assertNotIn('smoke', data)
                cases = engineering_checks(row['name'])['smoke']
                self.assertTrue(cases)
                self.assertTrue(all(('command' in case or 'operation' in case) for case in cases))
                self.assertTrue(all(case['expect'] is not None for case in cases if 'expect' in case))
                self.assertEqual(validate_manifest(data, ROOT / row['path']), [])

    def test_public_engineering_fields_are_rejected(self):
        for key in ['smoke', 'priority', 'wave', 'base', 'generation', 'parameters']:
            data = copy.deepcopy(self.data); data[key] = []
            self.assertTrue(self.check(data))

    def test_source_image_reference_are_exclusive(self):
        for branch in ['image', 'reference']:
            data = copy.deepcopy(self.data); data['sandbox']['template'][branch] = 'existing'
            self.assertTrue(self.check(data))

    def test_unknown_fields_and_wrong_types_are_rejected(self):
        for key, value in [('timeout', True), ('timeout', 0), ('unknown', 1), ('envs', [])]:
            data = copy.deepcopy(self.data); data['sandbox'].setdefault('instance', {})[key] = value
            self.assertTrue(self.check(data))

    def test_rejects_paths_outside_source_and_missing_files(self):
        for path in ['../outside', '/absolute', 'C:/absolute', 'a/../../b', 'a\\b', 'a\x00b', 'missing']:
            data = copy.deepcopy(self.data); data['sandbox']['template']['source']['dockerfile'] = path
            self.assertTrue(self.check(data))
        (self.root / 'outside').write_text('FROM example\n')
        (self.template / 'escape').symlink_to(self.root / 'outside')
        data = copy.deepcopy(self.data); data['sandbox']['template']['source']['dockerfile'] = 'escape'
        self.assertTrue(self.check(data))

    def test_symlink_loop_fails_as_validation_error(self):
        (self.template / 'loop').symlink_to('loop')
        self.data['sandbox']['template']['source']['dockerfile'] = 'loop'
        self.assertTrue(self.check())

    def test_native_serving_project_keeps_props_and_expressions(self):
        data = {'specVersion': 1, 'name': 'web', 'deployment': {'edition': '3.0.0', 'access': 'default', 'resources': {'api': {'component': 'fc3@0.1.26', 'props': {'memorySize': "${env('MEMORY')}", 'vpcConfig': {'vpcId': 'vpc-example'}}}}}}
        self.assertEqual(validate_manifest(data), [])
        self.assertEqual(data['deployment']['resources']['api']['props']['memorySize'], "${env('MEMORY')}")
        data['sandbox'] = self.data['sandbox']
        self.assertEqual(validate_manifest(data), [])  # Independent declarations are valid intent; consumers gate execution.

    def test_static_checker_preserves_numeric_expressions_without_environment_resolution(self):
        self.data['sandbox']['template']['props'] = {'cpu': "${env('CPU')}", 'memory': "${env('MEMORY')}"}
        (self.template / 'template.yaml').write_text(yaml.safe_dump(self.data))
        (self.template / '.env').write_text('CPU=not-a-number\nMEMORY=not-a-number\n')
        with patch('subprocess.run', side_effect=AssertionError('must not execute')), patch('subprocess.Popen', side_effect=AssertionError('must not execute')):
            self.assertEqual(check_template.check_directory(self.template), [])

    def test_unknown_versions_cannot_bypass_all_mode(self):
        for version in [2, 3, 5, 6, 999, None, False, '1']:
            data = copy.deepcopy(self.data); data['specVersion'] = version
            (self.template / 'template.yaml').write_text(yaml.safe_dump(data))
            self.assertTrue(check_template.claims_spec(self.template))
            self.assertEqual(check_template.main(['--all', '--root', str(self.root)]), 1)

    def test_design_and_catalog_gates_remain(self):
        self.data['name'] = 'sample'; renamed = self.root / 'sample'; self.template.rename(renamed)
        (renamed / 'template.yaml').write_text(yaml.safe_dump(self.data))
        (self.root / 'awesome-templates.yaml').write_text('schema_version: 3\ntemplates: []\n')
        codes = {item.code for item in check_template.check_directory(renamed)}
        self.assertIn('index', codes); self.assertIn('design-doc', codes)

    def test_duplicate_keys_and_malformed_manifests_cannot_hide_version(self):
        for suffix in ['specVersion: 4\n', 'application: [\n']:
            (self.template / 'template.yaml').write_text(yaml.safe_dump(self.data) + suffix)
            self.assertTrue(check_template.claims_spec(self.template))
            self.assertIn('yaml-parse', {item.code for item in check_template.check_directory(self.template)})

    def test_checker_never_executes_hooks_or_cloud(self):
        with patch('subprocess.run', side_effect=AssertionError('must not execute')), patch('subprocess.Popen', side_effect=AssertionError('must not execute')):
            self.assertEqual(check_template.check_directory(self.template), [])


if __name__ == '__main__':
    unittest.main()
