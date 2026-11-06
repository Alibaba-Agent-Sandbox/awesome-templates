"""Static managed manifest boundaries, independent of SDK and product recipes."""
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
from unittest.mock import patch

import run_local_e2e
from template_application import MANAGED_SCHEMA_PATH, validate_manifest, validate_v5, validate_v6

ROOT = Path(__file__).resolve().parents[1]


def managed_application() -> dict:
    targets = {
        "state": ["gateway", "worker", "dispatcher"],
        "sandboxAccess": ["worker", "dispatcher"], "model": ["sandbox-creation"],
        "clientAuth": ["gateway"], "internalAuth": ["gateway", "worker", "dispatcher"],
        "ingress": ["deployment-publisher"],
    }
    bindings = {name: {"reference": "test-" + name, "targets": value} for name, value in targets.items()}
    bindings["model"].update({"resolverRole": "worker", "allowedEnv": ["OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL"]})
    return {
        "api": {"protocol": "agent-sandbox-managed-agents/v1", "compatibility": "openai-agents-inspired-subset",
                "busyInputPolicy": "reject-unless-steerable", "explicitQueue": True},
        "runtime": {"placement": "in-sandbox", "driver": "sandbox-local-api", "profile": "managed-bridge-v1"},
        "gateway": {"placement": "fc-web"},
        "sandbox": {"provider": "alicloud-express", "lifetime": "per-session", "workspace": "exclusive",
                    "requiredFeatures": ["sandbox.lifecycle", "ports.url"]},
        "sessions": {"idleTimeoutSeconds": 900, "maxLifetimeSeconds": 3600, "maxLogicalSessionsPerOwner": 100,
                     "maxActiveSessions": 20, "maxQueuedTurnsPerSession": 8, "maxConcurrentTurnsPerSession": 1,
                     "resultRetentionSeconds": 86400, "closePolicy": "release-compute-retain-results",
                     "deletePolicy": "remove-public-data-retain-private-cleanup", "guestRestartPolicy": "freeze-and-reconcile"},
        "state": {"profile": "durable", "bindingRef": "state"},
        "storage": {"backend": "bounded-database", "maxFileBytes": 10485760, "maxArtifactBytes": 10485760,
                    "maxTurnArtifactBytes": 10485760, "maxRetainedBytesPerOwner": 104857600},
        "bindings": bindings,
        "limits": {"maxRunSeconds": 600, "maxToolSeconds": 60, "maxConcurrentRuns": 10, "maxQueuedRuns": 80,
                   "maxRunsPerMinute": 60, "maxEventsPerRun": 10000, "maxOutputBytes": 8388608, "maxSubscribersPerSession": 4},
        "deployment": {"profile": "fc-managed-agents", "accessRef": "default", "region": "cn-hangzhou",
                       "component": "fc3@0.1.26", "serverBuildRecipe": {"dockerfile": "server/Dockerfile", "context": "."},
                       "ingressBindingRef": "ingress", "revisionStrategy": "immutable-workers-with-drain"},
        "outputs": {"endpoint": {"from": "publish.outputs.endpoint"}, "protocol": "agent-sandbox-managed-agents/v1"},
    }


class ManagedApplicationContractTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.template = self.root / "_skeleton"
        shutil.copytree(ROOT / "_skeleton", self.template)
        (self.template / "server").mkdir()
        (self.template / "server/Dockerfile").write_text("FROM python:3.13.8-slim-bookworm\n")
        self.legacy = check_template.yaml.safe_load((self.template / "template.yaml").read_text())
        self.data = copy.deepcopy(self.legacy)
        self.data.update({"spec_version": 6, "start_cmd": "python -m agent_sandbox.server.managed --port 9000",
                          "ready_cmd": "agent-sandbox-server healthcheck --port 9000", "application": managed_application(),
                          "smoke": [{"operation": "health", "expect": {"status": "ok"}}],
                          "provides": {"app": {"protocol": "agent-sandbox-managed-bridge", "version": 1, "port": 9000,
                                                "operations": ["health", "capabilities"]}}})

    def validate(self):
        return validate_manifest(self.data, self.template)

    def test_closed_schema_and_existing_version_are_independent(self):
        from jsonschema import Draft202012Validator
        Draft202012Validator.check_schema(json.loads(MANAGED_SCHEMA_PATH.read_text()))
        self.assertEqual(self.validate(), [])
        self.assertEqual(validate_manifest(self.legacy, self.template), [])
        self.assertTrue(validate_v5(self.data, self.template))
        self.assertTrue(validate_v6(self.legacy, self.template))
        downgraded = copy.deepcopy(self.data)
        downgraded["spec_version"] = 5
        self.assertTrue(validate_manifest(downgraded, self.template))

    def test_complete_checker_uses_managed_documentation_and_smoke_contract(self):
        (self.template / "template.yaml").write_text(check_template.yaml.safe_dump(self.data))
        import re
        for name, cli, sdk, http in (
            ("README.md", "Quick start (CLI)", "Quick start (Python SDK)", "Quick start (HTTP POST)"),
            ("README.zh-CN.md", "快速开始（CLI）", "快速开始（Python SDK）", "快速开始（HTTP POST）"),
        ):
            target = self.template / name
            text = target.read_text()
            replacements = {cli: "abx app plan template.yaml", sdk: "pip install httpx==0.28.1\nimport httpx\nclient.post('/v1/agents/sessions')",
                            http: 'POST /v1/agents/sessions\nContent-Type: application/json'}
            for heading, body in replacements.items():
                text = re.sub(r"(?ms)(^## " + re.escape(heading) + r"\s*\n).*?(?=^## |\Z)",
                              lambda match: match.group(1) + "\n" + body + "\n\n", text)
            target.write_text(text)
        self.assertEqual(check_template.check_directory(self.template), [])
        self.data["start_cmd"] += " --unsafe-option"
        (self.template / "template.yaml").write_text(check_template.yaml.safe_dump(self.data))
        self.assertTrue(any(item.code == "yaml-start" for item in check_template.check_directory(self.template)))

    def test_legacy_local_runner_rejects_managed_startup_before_any_preparation(self):
        manifest = self.template / "template.yaml"
        manifest.write_text(check_template.yaml.safe_dump(self.data))
        with patch.object(run_local_e2e, "_missing_imports") as imports, patch.object(run_local_e2e, "_free_port") as port, patch.object(run_local_e2e.subprocess, "Popen") as process:
            status, detail = run_local_e2e._run_one(self.template, "")
        self.assertEqual(status, "fail")
        self.assertIn("Unsupported startup profile", detail)
        imports.assert_not_called(); port.assert_not_called(); process.assert_not_called()
        manifest.write_text(check_template.yaml.safe_dump(self.legacy))
        with patch.object(run_local_e2e, "_missing_imports", return_value=["fixture dependency"]) as imports:
            status, detail = run_local_e2e._run_one(self.template, "")
        self.assertEqual(status, "fail")
        self.assertIn("fixture dependency", detail)
        imports.assert_called_once()

    def test_local_runner_can_be_loaded_by_file_without_package_or_sibling_import_path(self):
        source = ROOT / "scripts/run_local_e2e.py"
        code = ("import importlib.util, sys; "
                "spec = importlib.util.spec_from_file_location('independent_local_runner', sys.argv[1]); "
                "module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); "
                "assert callable(module._run_one)")
        result = subprocess.run([sys.executable, "-I", "-c", code, str(source)], cwd=self.root,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_wrong_profile_topology_or_command_smoke_is_rejected(self):
        for key, value in (("runtime", {"placement": "in-sandbox", "driver": "sandbox-local-api", "profile": "server-core-agents"}),
                           ("gateway", {"placement": "client-direct"}),
                           ("state", {"profile": "ephemeral", "bindingRef": "state"})):
            with self.subTest(key=key):
                data = copy.deepcopy(self.data); data["application"][key] = value
                self.assertTrue(validate_manifest(data))
        self.data["smoke"] = [{"command": "agents_version", "expect": "diagnostic"}]
        self.assertTrue(self.validate())

    def test_server_build_and_frozen_image_are_exclusive(self):
        deployment = self.data["application"]["deployment"]
        deployment["serverImage"] = "registry.example/server@sha256:" + "a" * 64
        self.assertTrue(self.validate())
        del deployment["serverBuildRecipe"]
        self.assertEqual(self.validate(), [])
        deployment["serverImage"] = "registry.example/server:latest"
        self.assertTrue(self.validate())

    def test_missing_or_privilege_crossing_binding_is_rejected(self):
        for mutation in ("missing", "target", "environment", "state-reference"):
            with self.subTest(mutation=mutation):
                data = copy.deepcopy(self.data)
                bindings = data["application"]["bindings"]
                if mutation == "missing":
                    del bindings["model"]
                elif mutation == "target":
                    bindings["model"]["targets"].append("gateway")
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
        app["deployment"]["serverBuildRecipe"]["dockerfile"] = "../outside/Dockerfile"
        self.assertTrue(self.validate())
        outside = self.root / "outside"; outside.mkdir(); (outside / "Dockerfile").write_text("FROM example\n")
        (self.template / "escape").symlink_to(outside, target_is_directory=True)
        app["deployment"]["serverBuildRecipe"]["dockerfile"] = "escape/Dockerfile"
        self.assertTrue(self.validate())

    def test_unknown_fields_and_false_protocol_claim_are_rejected(self):
        self.data["application"]["deployment"]["steps"] = {}
        self.assertTrue(self.validate())
        del self.data["application"]["deployment"]["steps"]
        self.data["provides"]["app"]["protocol"] = "agent-sandbox-server"
        self.assertTrue(self.validate())


if __name__ == "__main__":
    unittest.main()
