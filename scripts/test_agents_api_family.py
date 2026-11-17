"""Exercise standalone Harness bootstraps and private credential boundaries."""
from __future__ import annotations

import importlib.util
import asyncio
import json
from pathlib import Path
import shutil
import os
import re
import subprocess
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from sync_agents_api_templates import PROFILES

ROOT = Path(__file__).resolve().parents[1]


def load_bootstrap(path):
    spec = importlib.util.spec_from_file_location("isolated_bootstrap", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HarnessFamilyTests(unittest.TestCase):
    def test_actual_guest_npm_run_commands_execute_without_shell_tokens(self):
        # Run the exact Dockerfile shell instruction against bounded stand-ins.
        # This detects malformed generated shell, without pretending to build an image.
        for adapter, profile in PROFILES.items():
            with self.subTest(adapter=adapter), tempfile.TemporaryDirectory() as directory:
                bin_dir = Path(directory)
                for binary in ("npm", profile["binary"]):
                    path = bin_dir / binary
                    if binary == "npm":
                        path.write_text("#!/bin/sh\ncase \"$*\" in\n"
                            + '"install -g ' + profile["package"] + "@" + profile["version"] + '"|"cache clean --force") exit 0;;\n'
                            + "*) exit 17;;\nesac\n")
                    else:
                        path.write_text('#!/bin/sh\n[ "$#" -eq 1 ] && [ "$1" = "--version" ]\n')
                    path.chmod(0o700)
                docker = (ROOT / ("agents-api-" + adapter) / "Dockerfile").read_text()
                command = re.search(r"(?ms)^RUN npm install -g (.*?)(?=\n\n)", docker).group(1)
                result = subprocess.run(["/bin/sh", "-ec", "npm install -g " + command],
                    env={"PATH": str(bin_dir) + os.pathsep + "/usr/bin:/bin"},
                    cwd=directory, capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode, 0, result.stderr)
                broken = command.replace("\\\n    &&", "\\\n+    &&")
                self.assertNotEqual(broken, command)
                control = subprocess.run(["/bin/sh", "-ec", "npm install -g " + broken],
                    env={"PATH": str(bin_dir) + os.pathsep + "/usr/bin:/bin"},
                    cwd=directory, capture_output=True, text=True, timeout=5)
                self.assertNotEqual(control.returncode, 0)

    def test_downloaded_projects_load_without_sibling_sources_and_isolate_keys(self):
        from agent_sandbox.managed_agents.models import ManagedConfig
        from agent_sandbox.managed_agents import ManagedService, ManagedStore
        from agent_sandbox.providers import ManagedExpressBackend

        for adapter, profile in PROFILES.items():
            with self.subTest(adapter=adapter), tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / "project"
                shutil.copytree(ROOT / ("agents-api-" + adapter), target)
                (target / "registry.yaml").unlink()
                bootstrap = load_bootstrap(target / "server/bootstrap.py")
                env = {
                    "AGENTS_APPLICATION": "isolated-application", "AGENTS_REVISION": "rev-test",
                    "AGENTS_TEMPLATE": "test-template", "AGENTS_MODEL": "test-model",
                    "AGENTS_ADAPTER": adapter, "ABX_MANAGED_DATABASE_URL": "sqlite:///:memory:",
                    "ABX_MANAGED_INTERNAL_TOKEN": "i" * 40, "AGENTS_BUSINESS_SHA256": "a" * 64,
                    "SANDBOX_API_KEY": "placeholder-platform", "SANDBOX_BASE_URL": "https://sandbox.example",
                    "SANDBOX_DOMAIN": "sandbox.example", "SANDBOX_REGION": "cn-hangzhou",
                    profile["keyEnv"]: "placeholder-model-credential",
                }
                if profile["baseUrlEnv"]:
                    env[profile["baseUrlEnv"]] = "https://model.example/api"
                gateway = bootstrap.compile_environment(env, "gateway")
                dispatcher = bootstrap.compile_environment(env, "dispatcher")
                worker = bootstrap.compile_environment(env, "worker")
                self.assertEqual(set(gateway), {"ABX_MANAGED_CONFIG_JSON", "ABX_MANAGED_AUTH_JSON"})
                self.assertNotIn("ABX_MANAGED_MODEL_CONFIG_JSON", dispatcher)
                self.assertNotIn("placeholder-model-credential", json.dumps([gateway, dispatcher]))
                config = ManagedConfig.from_dict(json.loads(worker["ABX_MANAGED_CONFIG_JSON"]))
                self.assertEqual(config.models, {"test-model": adapter})
                model = json.loads(worker["ABX_MANAGED_MODEL_CONFIG_JSON"])
                backend = ManagedExpressBackend(json.loads(worker["ABX_MANAGED_PROVIDER_CONFIG_JSON"]), model)
                self.assertEqual(backend.model["adapter"], adapter)
                # Use the real Session snapshot rather than hand-writing the private
                # allowlist: missing bootstrap admission must fail this regression.
                store = ManagedStore("sqlite:///" + str(Path(directory) / "state.sqlite"), config.application_id, local=True)
                service = ManagedService(store, config)
                session, _ = service.create_session("test-owner", {"agent": {"model": "test-model"}})
                with store.transaction() as tx:
                    frozen = tx.get(session["id"], "test-owner")
                class NativeInfrastructureReached(Exception):
                    pass
                with patch.object(backend, "_infra", AsyncMock(side_effect=NativeInfrastructureReached)):
                    with self.assertRaises(NativeInfrastructureReached):
                        asyncio.run(backend.create(frozen, "private-token", lambda resource: None))
                if adapter == "qoder":
                    self.assertNotIn("baseUrl", model)
                del env[profile["keyEnv"]]
                with self.assertRaisesRegex(ValueError, "credential"):
                    bootstrap.compile_environment(env, "worker")
                # Gateway readiness never requires a model key; only the worker executes it.
                bootstrap.compile_environment(env, "gateway")

    def test_harness_mismatch_fails_before_any_cloud_or_model_effect(self):
        bootstrap = load_bootstrap(ROOT / "agents-api-codex/server/bootstrap.py")
        with self.assertRaisesRegex(ValueError, "does not match"):
            bootstrap.compile_environment({
                "AGENTS_APPLICATION": "test", "AGENTS_REVISION": "rev-test", "AGENTS_TEMPLATE": "test",
                "AGENTS_MODEL": "test", "AGENTS_ADAPTER": "qoder", "ABX_MANAGED_DATABASE_URL": "test",
                "ABX_MANAGED_INTERNAL_TOKEN": "i" * 40,
            }, "gateway")


if __name__ == "__main__":
    unittest.main()
