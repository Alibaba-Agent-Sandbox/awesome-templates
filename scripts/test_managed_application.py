"""Managed manifest boundaries and declared local startup selection."""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import check_template
import yaml
from unittest.mock import patch

import run_local_e2e
from template_application import SCHEMA_PATH, validate_manifest

ROOT = Path(__file__).resolve().parents[1]


def managed_application() -> dict:
    return yaml.safe_load((ROOT / 'agents-api/template.yaml').read_text())['application']


class ManagedApplicationContractTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.template = self.root / "_skeleton"
        shutil.copytree(ROOT / "_skeleton", self.template)
        (self.template / "server").mkdir()
        (self.template / "server/Dockerfile").write_text("FROM python:3.13.8-slim-bookworm\n")
        self.legacy = yaml.safe_load((self.template / 'template.yaml').read_text())
        self.data = yaml.safe_load((ROOT / 'agents-api/template.yaml').read_text())
        self.data['name'] = 'example'


    def validate(self):
        return validate_manifest(self.data, self.template)

    def test_closed_schema_and_existing_version_are_independent(self):
        from jsonschema import Draft202012Validator
        Draft202012Validator.check_schema(json.loads(SCHEMA_PATH.read_text()))
        self.assertEqual(self.validate(), [])
        self.assertEqual(validate_manifest(self.legacy, self.template), [])
        self.assertNotIn("spec_version", self.data)
        downgraded = copy.deepcopy(self.data)
        downgraded["specVersion"] = 5
        self.assertTrue(validate_manifest(downgraded, self.template))

    def test_complete_checker_uses_managed_documentation_and_smoke_contract(self):
        (self.template / "template.yaml").write_text(yaml.safe_dump(self.data))
        import re
        for name, cli, sdk, http in (
            ("README.md", "Quick start (CLI)", "Quick start (Python SDK)", "Quick start (HTTP POST)"),
            ("README.zh-CN.md", "快速开始（CLI）", "快速开始（Python SDK）", "快速开始（HTTP POST）"),
        ):
            target = self.template / name
            text = target.read_text()
            replacements = {cli: "abx deploy . --name agents-api --plan", sdk: "pip install httpx==0.28.1\nimport httpx\nclient.post('/v1/agents/sessions')",
                            http: 'POST /v1/agents/sessions\nContent-Type: application/json'}
            for heading, body in replacements.items():
                text = re.sub(r"(?ms)(^## " + re.escape(heading) + r"\s*\n).*?(?=^## |\Z)",
                              lambda match: match.group(1) + "\n" + body + "\n\n", text)
            text = text.replace("Python SDK", "Python HTTP client" if name == "README.md" else "Python HTTP 客户端")
            target.write_text(text)

        with patch("template_application.engineering_checks", return_value={"smoke": [{"operation": "health", "expect": {"status": "ok"}}]}):
            self.assertEqual(check_template.check_directory(self.template), [])
        for name in ("README.md", "README.zh-CN.md"):
            target = self.template / name
            text = target.read_text()
            target.write_text(text.replace("httpx", "unrelated_client"))
            self.assertTrue(any(item.code == "readme-client" for item in check_template.check_directory(self.template)))
            target.write_text(text)
        self.data["sandbox"]["start"] = "python -m agent_sandbox.server.managed --port 9000 --unsafe-option"
        (self.template / "template.yaml").write_text(yaml.safe_dump(self.data))
        self.assertTrue(any(item.code == "yaml-schema" for item in check_template.check_directory(self.template)))

    def test_invalid_managed_startup_is_rejected_before_any_preparation(self):
        manifest = self.template / "template.yaml"
        invalid = copy.deepcopy(self.data)
        invalid["sandbox"]["start"] = "python -m agent_sandbox.server.managed --port 9000 --unsafe-option"
        manifest.write_text(yaml.safe_dump(invalid))
        with patch.object(run_local_e2e, "_missing_imports") as imports, patch.object(run_local_e2e, "_free_port") as port, patch.object(run_local_e2e.subprocess, "Popen") as process:
            status, detail = run_local_e2e._run_one(self.template, "")
        self.assertEqual(status, "fail")
        self.assertIn("invalid template manifest", detail)
        imports.assert_not_called(); port.assert_not_called(); process.assert_not_called()
        manifest.write_text(yaml.safe_dump(self.legacy))
        with patch.object(run_local_e2e, "_missing_imports", return_value=["fixture dependency"]) as imports:
            status, detail = run_local_e2e._run_one(self.template, "")
        self.assertEqual(status, "fail")
        self.assertIn("fixture dependency", detail)
        imports.assert_called_once()

    def test_local_runner_can_be_loaded_by_file_without_package_or_sibling_import_path(self):
        source = ROOT / "scripts/run_local_e2e.py"
        manifest = self.template / "template.yaml"
        manifest.write_text(yaml.safe_dump(self.data))
        code = ("import importlib.util, sys; "
                "from pathlib import Path; "
                "spec = importlib.util.spec_from_file_location('independent_local_runner', sys.argv[1]); "
                "module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); "
                "assert callable(module._run_one); "
                "assert module._startup_argv(Path(sys.argv[2]), 31234) == "
                "([sys.executable, '-m', 'agent_sandbox.server.managed', '--port', '31234'], True)")
        result = subprocess.run([sys.executable, "-I", "-c", code, str(source), str(self.template)], cwd=self.root,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_declared_managed_startup_and_legacy_argv_remain_distinct(self):
        manifest = self.template / "template.yaml"
        manifest.write_text(yaml.safe_dump(self.legacy))
        self.assertEqual(run_local_e2e._startup_argv(self.template, 31234), (["python3", "commands.py"], False))
        manifest.write_text(yaml.safe_dump(self.data))
        self.assertEqual(run_local_e2e._startup_argv(self.template, 31234),
                         ([sys.executable, "-m", "agent_sandbox.server.managed", "--port", "31234"], True))

    def test_duplicate_yaml_is_rejected_before_startup_preparation(self):
        manifest = self.template / "template.yaml"
        manifest.write_text(yaml.safe_dump(self.data) + "\nspecVersion: 1\n")
        with patch.object(run_local_e2e, "_missing_imports") as imports, patch.object(run_local_e2e, "_free_port") as port, patch.object(run_local_e2e.subprocess, "Popen") as process:
            status, detail = run_local_e2e._run_one(self.template, "")
        self.assertEqual(status, "fail")
        self.assertIn("valid template manifest", detail)
        imports.assert_not_called(); port.assert_not_called(); process.assert_not_called()

    def test_imported_local_runner_keeps_the_package_entry(self):
        code = ("from pathlib import Path; from scripts.run_local_e2e import _startup_argv; "
                "assert _startup_argv(Path('agents-api'), 31234)[1]")
        result = subprocess.run([sys.executable, "-c", code], cwd=ROOT,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_wrong_profile_topology_or_command_smoke_is_rejected(self):
        for key, value in (("runtime", {"placement": "in-sandbox", "driver": "sandbox-local-api", "profile": "server-core-agents"}),
                           ("gateway", {"placement": "client-direct"}),
                           ("state", {"profile": "ephemeral", "bindingRef": "state"})):
            with self.subTest(key=key):
                data = copy.deepcopy(self.data); data["application"][key] = value
                self.assertTrue(validate_manifest(data))
        self.data["application"]["smoke"] = [{"command": "agents_version", "expect": "diagnostic"}]
        self.assertTrue(self.validate())

    def test_server_build_and_frozen_image_are_exclusive(self):
        deployment = self.data["application"]["server"]
        deployment["image"] = "registry.example/server@sha256:" + "a" * 64
        self.assertTrue(self.validate())
        del deployment["source"]
        self.assertEqual(self.validate(), [])
        deployment["image"] = "registry.example/server:latest"
        self.assertTrue(self.validate())

    def test_missing_or_privilege_crossing_binding_is_rejected(self):
        for mutation in ("missing", "target", "environment", "state-reference"):
            with self.subTest(mutation=mutation):
                data = copy.deepcopy(self.data)
                bindings = data["application"]["bindings"]
                if mutation == "missing":
                    del bindings["model"]
                elif mutation == "target":
                    bindings["model"]["targets"] = ["gateway"]
                elif mutation == "environment":
                    bindings["model"]["allowedEnv"] = ["ALIBABA_CLOUD_ACCESS_KEY_SECRET"]
                else:
                    data["application"]["state"]["bindingRef"] = "model"
                self.assertTrue(validate_manifest(data))

    def test_budget_and_serial_session_constraints(self):
        for field, value in (("maxConcurrentTurnsPerSession", 2), ("idleTimeoutSeconds", 4000), ("maxLifetimeSeconds", 600)):
            with self.subTest(field=field):
                data = copy.deepcopy(self.data); data["application"]["sessions"][field] = value
                self.assertTrue(validate_manifest(data))
        self.data["application"]["limits"]["maxToolSeconds"] = 601
        self.assertTrue(self.validate())

    def test_hook_cannot_deploy_or_escape_sources(self):
        app = self.data["application"]
        app["hooks"] = {"afterReady": [{"id": "info", "type": "serverless-devs", "step": "gateway", "command": "info", "timeoutSeconds": 30}]}
        self.assertEqual(self.validate(), [])
        app["hooks"]["afterReady"][0]["command"] = "deploy"
        self.assertTrue(self.validate())
        del app["hooks"]
        app["server"]["source"]["dockerfile"] = "../outside/Dockerfile"
        self.assertTrue(self.validate())
        outside = self.root / "outside"; outside.mkdir(); (outside / "Dockerfile").write_text("FROM example\n")
        (self.template / "escape").symlink_to(outside, target_is_directory=True)
        app["server"]["source"]["dockerfile"] = "escape/Dockerfile"
        self.assertTrue(self.validate())

    def test_unknown_fields_and_false_protocol_claim_are_rejected(self):
        self.data["application"]["steps"] = {}
        self.assertTrue(self.validate())
        del self.data["application"]["steps"]
        self.data["sandbox"]["services"] = {"app": {"protocol": "agent-sandbox-server", "port": 9000, "version": 2, "operations": []}}
        self.assertTrue(self.validate())


if __name__ == "__main__":
    unittest.main()
