"""Canonical harness with synthetic CLI/SDK callbacks; no cloud acceptance."""
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from types import SimpleNamespace
from contextlib import contextmanager
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import express_e2e as harness


@contextmanager
def case():
    with tempfile.TemporaryDirectory(prefix="express-cleanup-unit-") as folder:
        root = Path(folder)
        project = root / "product"
        project.mkdir()
        (project / "template.yaml").write_text("name: product\nversion: 1.0.0\nsmoke:\n  - command: hello\n    expect: ok\n")
        options = harness.build_options([str(project), "--alias", "e2e-cleanup-regression"])
        intents = []
        original = harness.tempfile.mkdtemp
        def create(**kwargs):
            directory = original(dir=root, **kwargs)
            intents.append(Path(directory) / "intent.json")
            return directory
        with patch.object(harness.tempfile, "mkdtemp", create):
            yield project, options, intents


class CleanupTest(unittest.TestCase):
    def test_unknown_create_retains_template_until_sandbox_reconciliation(self):
        with case() as (project, options, intents):
            calls = []
            def runner(args, timeout):
                calls.append(args)
                if "--official-api" in args: return harness.Proc(0, "[]", "")
                if "deploy" in args: return harness.Proc(0, '{"TemplateID":"owned-template","Status":"ready"}', "")
                if "create" in args: return harness.Proc(1, "", "synthetic unknown response")
                self.fail("unknown create must reconcile before any cloud delete")
            with patch.object(harness, "recover_owned", return_value=False) as recovery:
                self.assertEqual(harness.execute(options, runner=runner, sdk=lambda *a: "ok"), 1)
                recovery.assert_called_once()
            self.assertFalse(any("delete" in args for args in calls))
            intent = json.loads(intents[0].read_text())
            self.assertEqual(intent["template_ids"], ["owned-template"])
            self.assertEqual(intent["sandbox_ids"], [])
            self.assertIs(intent["recovery_complete"], False)

    def test_sdk_recovery_paginates_and_kills_only_owned_template(self):
        from agent_sandbox import Sandbox
        calls = []
        killed = []
        async def listing(**kwargs):
            calls.append(kwargs["offset"])
            unrelated = [SimpleNamespace(template="other-template", sandbox_id=f"other-{i}") for i in range(99)]
            if kwargs["offset"]:
                return [SimpleNamespace(template="other-template", sandbox_id="other-last")]
            return unrelated + ([] if killed else [SimpleNamespace(template="owned-template", sandbox_id="owned-sandbox")])
        async def kill(sandbox_id, **kwargs):
            self.assertEqual(kwargs["provider"], "alicloud-express")
            killed.append(sandbox_id)
        with patch.object(Sandbox, "list", listing), patch.object(Sandbox, "kill_by_id", kill):
            self.assertEqual(harness._recover_sandboxes({"owned-template"}, set()), {"owned-sandbox"})
        self.assertEqual(killed, ["owned-sandbox"])
        self.assertIn(100, calls)

    def test_completed_cli_reaps_redirected_descendants(self):
        for code in (0, 7):
            with self.subTest(exit=code), tempfile.TemporaryDirectory() as directory:
                marker = Path(directory) / "survived"
                child = f"import time;time.sleep(1);open({str(marker)!r},'w').write('bad')"
                leader = "import subprocess,sys;subprocess.Popen([sys.executable,'-c'," + repr(child) + "],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);sys.exit(" + str(code) + ")"
                result = harness.run_monitored([sys.executable, "-c", leader], idle_timeout=5, wall_timeout=5)
                self.assertEqual(result.returncode, code)
                time.sleep(1.2)
                self.assertFalse(marker.exists())

    def test_cleanup_failure_never_writes_provider_pass(self):
        for operation, raises in [("kill", False), ("delete", False), ("kill", True), ("delete", True)]:
            with self.subTest(operation=operation, raises=raises), case() as (project, options, intents):
                recovered = []
                def runner(args, timeout):
                    if "--official-api" in args: return harness.Proc(0, "[]", "")
                    if "deploy" in args: return harness.Proc(0, '{"TemplateID":"owned-template","Status":"ready"}', "")
                    if "create" in args: return harness.Proc(0, '{"ID":"owned-sandbox"}', "")
                    if "run" in args: return harness.Proc(0, '{"result":"ok"}', "")
                    if operation in args:
                        if raises: raise RuntimeError("synthetic cleanup rejection")
                        return harness.Proc(7, "", "synthetic cleanup rejection")
                    return harness.Proc(0, "", "")
                with patch.object(harness, "recover_owned", lambda intent, run: recovered.append(intent.copy()) or True):
                    self.assertEqual(harness.execute(options, runner=runner, sdk=lambda *a: "ok"), 1)
                self.assertFalse((project / "evidence").exists())
                intent = json.loads(intents[0].read_text())
                self.assertEqual(intent["result"], "FAIL")
                self.assertIs(intent["cleanup_complete"], False)
                self.assertIs(intent["recovery_complete"], True)
                self.assertTrue(recovered)
                self.assertEqual(intent["template_ids"], ["owned-template"])
                self.assertEqual(intent["sandbox_ids"], ["owned-sandbox"])
                self.assertEqual(intents[0].stat().st_mode & 0o077, 0)

    def test_preexisting_alias_is_never_deployed_or_deleted(self):
        with case() as (project, options, intents):
            calls = []
            def runner(args, timeout):
                calls.append(args)
                return harness.Proc(0, '[{"TemplateID":"unrelated-template","Name":"e2e-cleanup-regression"}]', "")
            with patch.object(harness, "stop_deploy_processes") as stop, patch.object(harness, "_cleanup") as cleanup:
                self.assertEqual(harness.execute(options, runner=runner, sdk=lambda *a: "ok"), 2)
                stop.assert_not_called()
                cleanup.assert_not_called()
            self.assertEqual(len(calls), 1)
            self.assertIn("--official-api", calls[0])
            self.assertFalse((project / "evidence").exists())

    def test_failed_preflight_does_not_mutate_unowned_process_or_marker(self):
        with case() as (project, options, intents):
            marker = project / "Dockerfile.abx-build"
            def runner(args, timeout):
                marker.write_text("concurrent unowned marker")
                return harness.Proc(1, "", "synthetic list rejection")
            with patch.object(harness, "stop_deploy_processes") as stop, patch.object(harness, "_cleanup") as cleanup:
                self.assertEqual(harness.execute(options, runner=runner, sdk=lambda *a: "ok"), 1)
                stop.assert_not_called()
                cleanup.assert_not_called()
            self.assertEqual(marker.read_text(), "concurrent unowned marker")

    def test_recovery_uses_exact_alias_and_ignores_unrelated_template(self):
        rows = [{"TemplateID":"owned-template","Name":"e2e-cleanup-regression"},
                {"TemplateID":"other-template","Name":"e2e-cleanup-regression-other"}]
        calls = []
        def runner(args, timeout):
            calls.append(args)
            if "--official-api" in args: return harness.Proc(0, json.dumps(rows), "")
            self.assertEqual(args, ["template", "delete", "owned-template", "-y"])
            rows.pop(0)
            return harness.Proc(0, "", "")
        seen = []
        intent = {"alias":"e2e-cleanup-regression", "ownership_confirmed":True,
                  "deploy_attempted":True, "create_attempted":True, "template_ids":[], "sandbox_ids":[]}
        with patch.object(harness, "_recover_sandboxes", lambda ids, known: seen.append((ids, known)) or {"recovered-sandbox"}):
            self.assertTrue(harness.recover_owned(intent, runner))
        self.assertEqual(seen, [({"owned-template"}, set())])
        self.assertEqual(intent["sandbox_ids"], ["recovered-sandbox"])
        self.assertFalse(any("other-template" in call for call in calls))

    def test_empty_inventory_does_not_prove_ambiguous_request_clean(self):
        for create in (False, True):
            with self.subTest(create=create):
                intent = {"alias":"e2e-cleanup-regression", "ownership_confirmed":True,
                          "deploy_attempted":True, "create_attempted":create,
                          "template_ids":["owned-template"] if create else [], "sandbox_ids":[]}
                def runner(args, timeout):
                    self.assertIn("--official-api", args)
                    return harness.Proc(0, "[]", "")
                with patch.object(harness, "_recover_sandboxes", lambda *args: set()):
                    self.assertIs(harness.recover_owned(intent, runner), False)

    def test_success_publishes_only_after_cleanup(self):
        with case() as (project, options, intents):
            calls = []
            def runner(args, timeout):
                calls.append(args)
                self.assertFalse((project / "evidence").exists())
                if "--official-api" in args: return harness.Proc(0, "[]", "")
                if "deploy" in args:
                    self.assertEqual(args[args.index("--acr-repo") + 1], options.alias)
                    self.assertEqual(args[args.index("--tag") + 1], "review")
                    self.assertNotEqual(args[args.index("--acr-repo") + 1], "product")
                    return harness.Proc(0, '{"TemplateID":"owned-template","Status":"ready"}', "")
                if "create" in args: return harness.Proc(0, '{"ID":"owned-sandbox"}', "")
                if "run" in args: return harness.Proc(0, '{"result":"ok"}', "")
                return harness.Proc(0, "", "")
            self.assertEqual(harness.execute(options, runner=runner, sdk=lambda *a: "ok"), 0)
            self.assertEqual(len(list((project / "evidence").glob("express-*.json"))), 1)
            self.assertFalse(intents[0].exists())
            self.assertEqual(calls[-2:], [["kill", "owned-sandbox", "-y"], ["template", "delete", "owned-template", "-y"]])


if __name__ == "__main__":
    unittest.main()
