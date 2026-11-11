"""Cross-language fixtures and rejection of ambiguous authored manifests."""
import copy
import json
import subprocess
import unittest
from pathlib import Path

from template_application import PROFILE_ROOT, PROFILE_CATALOG, is_managed_application, normalize_manifest, validate_v6


class ApplicationProfileTest(unittest.TestCase):
    def test_shared_python_and_javascript_fixtures(self):
        fixtures = json.loads((PROFILE_ROOT / "fixtures.json").read_text())
        for fixture in fixtures:
            with self.subTest(fixture=fixture["name"]):
                original = copy.deepcopy(fixture["input"])
                if fixture.get("error"):
                    with self.assertRaises(ValueError):
                        normalize_manifest(original)
                else:
                    normalized = normalize_manifest(original)
                    self.assertEqual(normalized, fixture["expected"])
                    self.assertEqual(normalize_manifest(normalized), normalized)
                self.assertEqual(original, fixture["input"])
        subprocess.run(["node", str(PROFILE_ROOT / "test.mjs")], check=True)

    def test_real_compact_manifest_preserves_expanded_runtime_contract(self):
        import yaml
        manifest = yaml.safe_load((PROFILE_ROOT.parents[1] / "agents-api/template.yaml").read_text())
        expected = json.loads((PROFILE_ROOT / "fixtures.json").read_text())[0]["expected"]
        expected["version"] = manifest["version"]
        self.assertEqual(normalize_manifest(manifest), expected)
        self.assertEqual(validate_v6(manifest), [])

    def test_explicit_conflicts_are_not_repaired(self):
        original = json.loads((PROFILE_ROOT / "fixtures.json").read_text())[1]["input"]
        for section, field, value in (("api", "explicitQueue", False), ("runtime", "placement", None),
                                      ("sessions", "maxConcurrentTurnsPerSession", 2),
                                      ("sandbox", "requiredFeatures", [])):
            manifest = copy.deepcopy(original)
            manifest["application"].setdefault(section, {})[field] = value
            self.assertEqual(normalize_manifest(manifest)["application"][section][field], value)
            self.assertTrue(validate_v6(manifest))
        for section in ("api", "runtime", "gateway", "outputs", "bindings"):
            manifest = copy.deepcopy(original)
            manifest["application"][section] = None
            self.assertTrue(validate_v6(manifest))

    def test_profile_selects_type_and_version_selects_validator(self):
        original = json.loads((PROFILE_ROOT / "fixtures.json").read_text())[1]["input"]
        self.assertEqual(validate_v6(original), [])
        original["spec_version"] = 5
        self.assertTrue(is_managed_application(original))
        self.assertTrue(validate_v6(original))
        del original["application"]["deployment"]["profile"]
        original["spec_version"] = 6
        self.assertFalse(is_managed_application(original))
        self.assertTrue(validate_v6(original))

    def test_required_features_can_extend_the_profile_minimum(self):
        manifest = json.loads((PROFILE_ROOT / "fixtures.json").read_text())[1]["input"]
        manifest["application"]["sandbox"]["requiredFeatures"] = ["ports.url", "sandbox.lifecycle", "files.rw"]
        self.assertEqual(validate_v6(manifest), [])
        self.assertEqual(normalize_manifest(manifest)["application"]["sandbox"]["requiredFeatures"],
                         ["ports.url", "sandbox.lifecycle", "files.rw"])

    def test_binding_defaults_preserve_security_boundaries(self):
        original = json.loads((PROFILE_ROOT / "fixtures.json").read_text())[1]["input"]
        for name, patch in (("model", {"targets": ["gateway"]}),
                            ("model", {"allowedEnv": ["ALIBABA_CLOUD_ACCESS_KEY_SECRET"]}),
                            ("clientAuth", {"resolverRole": "worker"})):
            manifest = copy.deepcopy(original)
            manifest["application"]["bindings"][name].update(patch)
            self.assertTrue(validate_v6(manifest))
        missing = copy.deepcopy(original)
        del missing["application"]["bindings"]["model"]
        self.assertTrue(validate_v6(missing))
        extra = copy.deepcopy(original)
        extra["application"]["bindings"]["other"] = {"reference": "extra"}
        self.assertTrue(validate_v6(extra))
