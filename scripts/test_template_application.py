#!/usr/bin/env python3
"""Observable v3 manifest compatibility and deployment validation regressions."""
from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import check_template
from template_application import SCHEMA_PATH, validate_v3

ROOT = Path(__file__).resolve().parents[1]


def local_application() -> dict:
    return {
        "runtime": {"placement": "in-sandbox", "driver": "sandbox-local-api", "profile": "server-core-agents"},
        "gateway": {"placement": "client-direct"}, "deployment": {"adapter": "none"},
        "sandbox": {"provider": "alicloud-express", "lifetime": "per-run", "workspace": "exclusive",
                    "requiredFeatures": ["sandbox.lifecycle", "ports.url"]},
        "state": {"profile": "ephemeral"}, "bindings": {},
        "limits": {"maxRunSeconds": 900, "maxToolSeconds": 60, "maxConcurrentRuns": 1,
                   "maxQueuedRuns": 8, "maxRunsPerMinute": 10, "maxEventsPerRun": 10000,
                   "maxOutputBytes": 8388608},
    }


def external_application() -> dict:
    application = local_application()
    application.update({
        "runtime": {"placement": "external", "driver": "python-remote-tools"},
        "gateway": {"placement": "fc-web"},
        "deployment": {"adapter": "serverless-devs-fc3", "project": "deploy/s.yaml",
                       "toolchainLock": "deploy/toolchain.lock.json", "accessRef": "deploy-access"},
        "state": {"profile": "durable", "bindingRef": "run-store"},
        "bindings": {"run-store": "run-database", "model-access": "model-token"},
    })
    application["sandbox"]["requiredFeatures"] = ["sandbox.lifecycle", "exec.run", "files.rw", "ports.url"]
    return application


class ApplicationContractTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.template = self.root / "_skeleton"
        shutil.copytree(ROOT / "_skeleton", self.template)
        self.data = check_template.yaml.safe_load((self.template / "template.yaml").read_text())
        self.data["spec_version"] = 3
        (self.template / "deploy").mkdir()
        (self.template / "deploy/s.yaml").write_text("edition: 3.0.0\n")
        (self.template / "deploy/toolchain.lock.json").write_text("{}\n")

    def check(self, data=None):
        return validate_v3(data or self.data, self.template)

    def test_schema_is_valid(self):
        from jsonschema import Draft202012Validator
        Draft202012Validator.check_schema(json.loads(SCHEMA_PATH.read_text()))

    def test_documented_examples_match_machine_contract(self):
        for name in ("application-local", "application-external"):
            with self.subTest(name=name):
                source = ROOT / "docs/examples" / name
                data = check_template.yaml.safe_load((source / "template.yaml").read_text())
                self.assertEqual(validate_v3(data, source), [])

    def test_v2_unchanged_and_v3_without_application(self):
        self.assertEqual(check_template.check_directory(ROOT / "_skeleton"), [])
        self.assertEqual(self.check(), [])
        (self.template / "template.yaml").write_text(check_template.yaml.safe_dump(self.data))
        self.assertEqual(check_template.check_directory(self.template), [])

    def test_existing_catalog_expectation_shapes_survive_v3_adoption(self):
        catalog = check_template.yaml.safe_load((ROOT / "awesome-templates.yaml").read_text())
        for entry in catalog["templates"]:
            source = ROOT / entry["path"]
            data = check_template.yaml.safe_load((source / "template.yaml").read_text())
            data["spec_version"] = 3
            data["smoke"] = [item for item in data["smoke"] if "expect" in item]
            if not data["smoke"]:
                continue  # V3 explicitly requires expectations; no declared shape to migrate.
            with self.subTest(template=entry["name"]):
                self.assertEqual(validate_v3(data, source), [])

    def test_v3_keeps_required_non_null_expectations(self):
        self.data["smoke"][0].pop("expect")
        self.assertTrue(self.check())
        self.data["smoke"][0]["expect"] = None
        self.assertTrue(self.check())

    def test_direct_external_and_managed_local_contracts(self):
        for application in (local_application(), external_application()):
            with self.subTest(application=application["runtime"]):
                self.data["application"] = application
                self.assertEqual(self.check(), [])
        self.data["application"] = external_application()
        self.data["application"]["runtime"] = local_application()["runtime"]
        self.assertEqual(self.check(), [])

    def test_illegal_combinations_types_unknown_fields_and_limits(self):
        cases = [
            ("runtime", "placement", "on-host"), ("runtime", "driver", "sandbox-local-api"),
            ("runtime", "profile", "server-core-agents"), ("gateway", "placement", "client-direct"),
            ("deployment", "adapter", "none"), ("deployment", "accessRef", "raw secret"),
            ("deployment", "unknown", "value"), ("state", "profile", "ephemeral"),
            ("state", "bindingRef", "missing"), ("sandbox", "workspace", "shared"),
            ("sandbox", "requiredFeatures", []), ("limits", "maxToolSeconds", 901),
            ("limits", "maxRunSeconds", True), ("limits", "maxEventsPerRun", 1),
            ("limits", "maxEventsPerRun", 4),
            ("limits", "maxOutputBytes", 10), ("limits", "typo", 3),
        ]
        for section, key, value in cases:
            with self.subTest(section=section,key=key):
                self.data["application"] = external_application()
                self.data["application"][section][key] = value
                self.assertTrue(self.check())
        self.data["application"] = local_application()
        self.data["application"]["state"] = {"profile": "durable", "bindingRef": "run-store"}
        self.assertTrue(self.check())

    def test_required_provider_feature_baselines(self):
        for factory, needed in ((local_application, ("sandbox.lifecycle", "ports.url")),
                                (external_application, ("sandbox.lifecycle", "exec.run", "files.rw"))):
            for feature in needed:
                with self.subTest(runtime=factory.__name__,feature=feature):
                    self.data["application"] = factory()
                    self.data["application"]["sandbox"]["requiredFeatures"].remove(feature)
                    self.assertTrue(self.check())

    def test_rejects_paths_outside_source_and_missing_files(self):
        for path in ("../outside", "/absolute", "C:/absolute", "a/../../b", "a\\b", "a\x00b", "missing"):
            with self.subTest(path=path):
                self.data["application"] = external_application()
                self.data["application"]["deployment"]["project"] = path
                self.assertTrue(self.check())
        (self.template / "outside.yaml").symlink_to(self.root / "outside.yaml")
        (self.root / "outside.yaml").write_text("edition: 3.0.0\n")
        self.data["application"] = external_application()
        self.data["application"]["deployment"]["project"] = "outside.yaml"
        self.assertTrue(self.check())

    def test_symlink_loop_fails_as_validation_error(self):
        (self.template / "loop").symlink_to("loop")
        self.data["application"] = external_application()
        self.data["application"]["deployment"]["project"] = "loop"
        self.assertTrue(self.check())

    def test_hook_types_phases_and_duplicates(self):
        hook = {"id": "smoke", "executor": "host-command", "argv": ["python3", "smoke.py"],
                "cwd": ".", "timeoutSeconds": 30, "envAllowlist": ["MODEL_TOKEN"]}
        self.data["application"] = external_application()
        self.data["application"]["hooks"] = {"afterReady": [hook]}
        self.assertEqual(self.check(), [])
        for key, value in (("argv", "python3 smoke.py"), ("executor", "shell"), ("cwd", ".."),
                           ("timeoutSeconds", 901), ("envAllowlist", ["bad-name"]), ("shell", True)):
            with self.subTest(key=key):
                self.data["application"]["hooks"] = {"afterReady": [{**hook,key:value}]}
                self.assertTrue(self.check())
        self.data["application"]["hooks"] = {"afterReady": [hook], "beforeApply": [hook]}
        self.assertTrue(self.check())
        self.data["application"]["hooks"] = {"onCreate": [hook]}
        self.assertTrue(self.check())
        self.data["application"] = local_application()
        self.data["application"]["hooks"] = {"afterReady": [hook]}
        self.assertTrue(self.check())

    def test_inline_deployment_and_project_are_exclusive_and_pinned(self):
        self.data["application"] = external_application()
        deployment = self.data["application"]["deployment"]
        del deployment["project"]
        self.assertTrue(self.check())
        deployment["inline"] = {"edition": "3.0.0", "name": "agent", "resources": {
            name: {"component": "fc3@1.2.3", "props": {"functionName": name}}
            for name in ("gateway", "worker", "dispatcher")}}
        self.assertEqual(self.check(), [])
        deployment["project"] = "deploy/s.yaml"
        self.assertTrue(self.check())
        del deployment["project"]
        deployment["inline"]["resources"]["worker"]["component"] = "fc3"
        self.assertTrue(self.check())
        deployment["inline"]["resources"]["worker"]["component"] = "fc3@1.2.3"
        del deployment["inline"]["resources"]["dispatcher"]
        self.assertTrue(self.check())

    def test_v3_and_unknown_versions_cannot_bypass_all_mode(self):
        self.data["application"] = external_application()
        self.data["application"]["unknown"] = True
        for version in (3, 999, None, False, "3"):
            with self.subTest(version=version):
                self.data["spec_version"] = version
                (self.template / "template.yaml").write_text(check_template.yaml.safe_dump(self.data))
                self.assertTrue(check_template.claims_spec(self.template))
                self.assertEqual(check_template.main(["--all", "--root", str(self.root)]), 1)
        self.data["spec_version"] = 2
        (self.template / "template.yaml").write_text(check_template.yaml.safe_dump(self.data))
        self.assertTrue(any(item.code == "yaml-schema" for item in check_template.check_directory(self.template)))

    def test_v3_retains_design_and_catalog_gates(self):
        self.data["name"] = "sample"
        self.data["application"] = local_application()
        renamed = self.root / "sample"
        self.template.rename(renamed)
        (renamed / "template.yaml").write_text(check_template.yaml.safe_dump(self.data))
        (self.root / "awesome-templates.yaml").write_text("templates: []\n")
        codes = {item.code for item in check_template.check_directory(renamed)}
        self.assertIn("index", codes)
        self.assertIn("design-doc", codes)
        (self.root / "awesome-templates.yaml").write_text(check_template.yaml.safe_dump({"templates": [{
            "name": "sample", "path": "sample", "status": "experimental", "capabilities": ["ports"]}]}))
        self.assertIn("index-capabilities", {item.code for item in check_template.check_directory(renamed)})

    def test_duplicate_keys_and_malformed_manifests_cannot_hide_version(self):
        for suffix in ("spec_version: 3\n", "application: [\n"):
            with self.subTest(suffix=suffix):
                (self.template / "template.yaml").write_text(check_template.yaml.safe_dump(self.data) + suffix)
                self.assertTrue(check_template.claims_spec(self.template))
                self.assertTrue(any(item.code == "yaml-parse" for item in check_template.check_directory(self.template)))
                self.assertEqual(check_template.main(["--all", "--root", str(self.root)]), 1)

    def test_v3_checker_never_executes_hook_or_cloud(self):
        self.data["application"] = external_application()
        (self.template / "template.yaml").write_text(check_template.yaml.safe_dump(self.data))
        with patch("subprocess.run", side_effect=AssertionError("must not execute")), patch("subprocess.Popen", side_effect=AssertionError("must not execute")):
            self.assertEqual(check_template.check_directory(self.template), [])


if __name__ == "__main__":
    unittest.main()
