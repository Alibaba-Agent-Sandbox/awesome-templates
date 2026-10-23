"""Current executable/parser and owned-cleanup regressions, without cloud calls."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import express_e2e as harness
from test_express_cleanup import case, cli_help


class ExpressCliContract(unittest.TestCase):
    def test_detached_id_is_one_identifier_not_json_or_terminal_output(self):
        for value in ("sb-owned_123\n", "\n sb-owned_123 \n"):
            self.assertEqual(harness.detached_sandbox_id(harness.Proc(0, value, "")), "sb-owned_123")
        for value in ("", '{"ID":"sb-owned"}', "ID: sb-owned", "hello\nsb-owned",
                      "opensandbox:sb-owned", "../sb-owned", "\x1b[31msb-owned", "x" * 257):
            with self.subTest(value=value):
                self.assertIsNone(harness.detached_sandbox_id(harness.Proc(0, value, "")))

    def test_reconciliation_matches_exact_standard_alias_and_fails_closed(self):
        rows = [{"templateID": "other", "aliases": ["owned-other"]},
                {"templateID": "owned-id", "aliases": ["secondary", "owned"]}]
        def run(args, timeout):
            self.assertEqual(args, ["template", "list", "--format", "json"])
            return harness.Proc(0, json.dumps(rows), "")
        self.assertEqual(harness.official_templates(run, "owned"), ["owned-id"])
        for row in ({"Name": "owned", "TemplateID": "legacy"},
                    {"templateID": "owned-id", "aliases": "owned"},
                    {"templateID": "", "aliases": ["owned"]}):
            rows[:] = [row]
            with self.assertRaises(RuntimeError):
                harness.official_templates(run, "owned")

    def test_contract_mismatch_prevents_deploy_and_cleanup(self):
        for failed in ("list", "kill", "create"):
            with self.subTest(failed=failed), case() as (project, options, intents):
                calls = []
                def run(args, timeout):
                    calls.append(args)
                    self.assertEqual(args[-1], "--help")
                    return harness.Proc(1, "", "unsupported") if failed in args else cli_help(args)
                # case() does not stub this guard; exercise execute's real ordering.
                with patch.object(harness, "_cleanup") as cleanup, patch.object(harness, "recover_owned") as recover:
                    self.assertEqual(harness.execute(options, runner=run), 1)
                    cleanup.assert_not_called()
                    recover.assert_not_called()
                self.assertFalse((project / "evidence").exists())
                intent = json.loads(intents[0].read_text())
                self.assertFalse(intent["deploy_attempted"])
                self.assertFalse(intent["create_attempted"])

    @unittest.skipUnless(os.environ.get("ABX"), "ABX executable required; CI provides the pinned CLI")
    def test_actual_executable_accepts_create_list_and_cleanup_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "template.yaml").write_text("name: contract-probe\nsmoke: [{command: hello}]\n")
            # Drop cloud credentials and target a non-routable endpoint. Help and
            # argument validation must complete without any backend request.
            env = {key: os.environ[key] for key in ("PATH", "ABX") if key in os.environ}
            env.update(HOME=directory, USERPROFILE=directory, NO_COLOR="1",
                       E2B_API_URL="https://api.example.invalid", E2B_DOMAIN="example.invalid")
            def run(args, timeout):
                proc = subprocess.run(harness._abx_argv(args), capture_output=True, text=True,
                                      cwd=directory, env=env, timeout=timeout)
                return harness.Proc(proc.returncode, proc.stdout, proc.stderr)
            options = harness.build_options([str(Path(directory)), "--sandbox-timeout", "60"])
            harness.validate_cli_contract(run, options)
            result = run(harness.cli_create_args("preflight-only", 29), 30)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--timeout must be at least 30 seconds", result.stderr)
            # Exercise the real cleanup helper, with --help appended at the
            # subprocess boundary to validate flags without deleting anything.
            calls = []
            def cleanup_run(args, timeout):
                calls.append(args)
                return run([*args, "--help"], timeout)
            self.assertTrue(harness._cleanup(cleanup_run, "owned-sandbox", "owned-template",
                                            Path(directory) / "Dockerfile.abx-build", False))
            self.assertEqual(calls, [["kill", "owned-sandbox"],
                                     ["template", "delete", "owned-template", "-y"]])


if __name__ == "__main__":
    unittest.main()
