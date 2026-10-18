"""Controller authorization/receipt/cleanup gates with fixtures; never cloud proof."""
import json
import os
from pathlib import Path
import tempfile
import sys
import time
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import canonical_express_review as review

APPROVAL = {"REVIEW_ENABLE":"approved", "REVIEW_HEAD":"a" * 40,
            "REVIEW_APPROVED_SHA":"a" * 40, "REVIEW_SAME_REPOSITORY":"true"}


class AuthorizationTest(unittest.TestCase):
    def test_disabled_wrong_head_and_fork_stay_blocked(self):
        approved = {"REVIEW_ENABLE":"approved", "REVIEW_HEAD":"a" * 40,
                    "REVIEW_APPROVED_SHA":"a" * 40, "REVIEW_SAME_REPOSITORY":"true"}
        self.assertTrue(review.authorization(approved)[0])
        for changes in ({"REVIEW_ENABLE":""}, {"REVIEW_APPROVED_SHA":"b" * 40},
                        {"REVIEW_SAME_REPOSITORY":"false"}, {"REVIEW_HEAD":""}):
            with self.subTest(changes=changes):
                self.assertFalse(review.authorization(approved | changes)[0])
        self.assertEqual(review.authorization({})[1], ["python-hello"])

    def test_explicit_small_or_full_matrix_only(self):
        self.assertEqual(review.select("python-hello,pi"), ["python-hello", "pi"])
        self.assertEqual(len(review.select("all")), 23)
        for text in ("", "../python-hello", "python-hello,python-hello", "python-hello;echo bad"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                review.select(text)

    def test_full_selection_matches_every_integrated_catalog_entry(self):
        import yaml
        root = Path(__file__).resolve().parents[1]
        catalog = yaml.safe_load((root / "awesome-templates.yaml").read_text())
        self.assertEqual(set(review.select("all")), {row["path"] for row in catalog["templates"]})

    def test_missing_credentials_never_calls_source_or_cloud(self):
        with tempfile.TemporaryDirectory() as directory:
            old = Path.cwd()
            try:
                os.chdir(directory)
                with patch.dict(os.environ, APPROVAL, clear=True), patch.object(review, "registry") as cloud, patch.object(review.subprocess, "check_output") as git:
                    self.assertEqual(review.run("python-hello"), 2)
                    cloud.assert_not_called()
                    git.assert_not_called()
                data = json.loads(Path("canonical-output/python-hello/status.json").read_text())
                self.assertEqual(data["result"], "BLOCKED")
                self.assertIs(data["cloud_executed"], False)
            finally:
                os.chdir(old)

    def test_existing_credentials_without_approval_do_not_start_cloud(self):
        with tempfile.TemporaryDirectory() as directory:
            old = Path.cwd()
            try:
                os.chdir(directory)
                env = {name:"synthetic-private-" + name for name in review.REQUIRED}
                with patch.dict(os.environ, env, clear=True), patch.object(review, "registry") as cloud, patch.object(review.subprocess, "check_output") as git:
                    self.assertEqual(review.run("python-hello"), 2)
                    cloud.assert_not_called()
                    git.assert_not_called()
            finally:
                os.chdir(old)


class ProcessTest(unittest.TestCase):
    def test_completed_and_timed_out_leaders_leave_no_owned_descendant(self):
        for code in (0, 7, None):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as directory:
                marker = Path(directory) / "descendant"
                child = "import signal,time,pathlib; signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(.6); pathlib.Path(" + repr(str(marker)) + ").touch()"
                leader = "import subprocess,sys,time,signal; subprocess.Popen([sys.executable,'-c'," + repr(child) + "],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); "
                leader += "signal.signal(signal.SIGINT,signal.SIG_IGN); time.sleep(20)" if code is None else "sys.exit(" + str(code) + ")"
                result = review.invoke([sys.executable,"-c",leader], dict(os.environ), timeout=.15 if code is None else 2, _grace=.05)
                self.assertEqual(result, 124 if code is None else code)
                time.sleep(.7)
                self.assertFalse(marker.exists())

    def test_proxy_ca_configuration_is_forwarded_without_model_keys(self):
        with patch.dict(os.environ, {"REQUESTS_CA_BUNDLE":"/owned/ca", "CURL_CA_BUNDLE":"/owned/ca", "OPENAI_API_KEY":"synthetic-unrelated"}, clear=True):
            env = review.child_environment(Path("/tmp/owned-controller-fixture"))
        self.assertEqual(env["REQUESTS_CA_BUNDLE"], "/owned/ca")
        self.assertEqual(env["CURL_CA_BUNDLE"], "/owned/ca")
        self.assertNotIn("OPENAI_API_KEY", env)


class ReceiptTest(unittest.TestCase):
    def exercise_runner_receipt(self, leak=False):
        with tempfile.TemporaryDirectory() as directory:
            old = Path.cwd()
            try:
                os.chdir(directory)
                runner = Path(directory) / "runner"
                runner.mkdir()
                source = Path("reviewed/templates/python-hello")
                source.mkdir(parents=True)
                (source / "template.yaml").write_text("name: python-hello\nversion: 1.0.0\nsmoke:\n  - command: hello\n    expect: ok\n")
                env = {name:"synthetic-private-" + name for name in review.REQUIRED}
                env.update(APPROVAL)
                env.update(RUNNER_TEMP=str(runner), GITHUB_RUN_ID="1", GITHUB_RUN_ATTEMPT="1")
                env.update(OPENAI_API_KEY="synthetic-unrelated-model-key", AIDER_API_KEY="synthetic-unrelated-aider-key")
                def invoke(argv, child_env, **kwargs):
                    self.assertNotIn("OPENAI_API_KEY", child_env)
                    self.assertNotIn("AIDER_API_KEY", child_env)
                    self.assertIn("--alias", argv)
                    day = (datetime.now(timezone.utc) + timedelta(days=1)).date().isoformat()
                    receipt = {"provider":"alicloud-express", "passed":True, "cleanup_verified":True, "template":"python-hello",
                        "template_version":"1.0.0", "date":day, "cli":"abx", "commands":[
                            {"name":"hello", "via":via, "ok":True,
                             "result":env["ABX_SANDBOX_API_KEY"] if leak else "ok"} for via in ("cli","sdk")]}
                    review.save(source / "evidence" / ("express-" + day + ".json"), receipt)
                    return 0
                with patch.dict(os.environ, env, clear=True), patch.object(review.subprocess, "check_output", side_effect=lambda args, **kwargs:review.PINS[Path(args[2]).name] + "\n"), patch.object(review, "registry", side_effect=FileNotFoundError), patch.object(review, "invoke", side_effect=invoke), patch.object(review, "delete_absent"):
                    code = review.run("python-hello")
                output = Path("canonical-output/python-hello")
                return code, json.loads((output / "status.json").read_text()), len(list(output.glob("express-*.json")))
            finally:
                os.chdir(old)

    def test_fresh_receipt_crossing_midnight_is_accepted(self):
        self.assertEqual(self.exercise_runner_receipt()[::2], (0, 1))

    def test_private_value_in_canonical_receipt_is_not_uploaded(self):
        code, status, receipts = self.exercise_runner_receipt(leak=True)
        self.assertEqual((code, status["result"], receipts), (1, "FAIL", 0))

    def exercise(self, *, code=0, registry=True, recovery=0, registry_failure=False):
        with tempfile.TemporaryDirectory() as directory:
            old = Path.cwd()
            try:
                os.chdir(directory)
                with patch.dict(os.environ, {"RUNNER_TEMP":directory, "ACR_NAMESPACE":"synthetic-namespace"}):
                    private = review.private_root("python-hello")
                    (private / "tmp").mkdir(parents=True)
                    candidate = Path(directory) / "express-2000-01-01.json"
                    candidate.write_text('{"passed":true}')
                    state = {"alias":"e2e-owned-unit-test", "registry_owned":registry,
                             "acr_repo":"e2e-owned-unit-test", "acr_tag":"review",
                             "canonical_exit":code, "canonical_evidence_checked":True, "candidate":str(candidate)}
                    review.save(private / "state.json", state, private=True)
                    if recovery:
                        intent = private / "tmp/abx-express-owned-synthetic/intent.json"
                        review.save(intent, {}, private=True)
                    with patch.object(review, "invoke", return_value=recovery), patch.object(review, "delete_absent", side_effect=RuntimeError("synthetic failure") if registry_failure else None) as delete:
                        result = review.finish("python-hello")
                    if delete.call_count == 2:
                        self.assertEqual([call.args[0] for call in delete.call_args_list],
                            ["/repos/synthetic-namespace/e2e-owned-unit-test/tags/review",
                             "/repos/synthetic-namespace/e2e-owned-unit-test"])
                        self.assertTrue(all("/python-hello" not in call.args[0] for call in delete.call_args_list))
                    output = Path("canonical-output/python-hello")
                    status = json.loads((output / "status.json").read_text())
                    return result, status, len(list(output.glob("express-*.json"))), delete.call_count
            finally:
                os.chdir(old)

    def test_failed_canonical_exit_cannot_reuse_pass_receipt(self):
        code, status, receipts, _ = self.exercise(code=1, registry=False)
        self.assertEqual((code, status["result"], receipts), (1, "FAIL", 0))

    def test_failed_compute_cleanup_preserves_registry_and_refuses_receipt(self):
        code, status, receipts, deletes = self.exercise(recovery=2)
        self.assertEqual((code, status["result"], receipts, deletes), (1, "FAIL", 0, 0))

    def test_failed_registry_cleanup_cannot_publish_provider_pass(self):
        code, status, receipts, _ = self.exercise(registry_failure=True)
        self.assertEqual((code, status["result"], receipts), (1, "FAIL", 0))

    def test_pass_requires_real_runner_exit_receipt_and_all_cleanup_gates(self):
        code, status, receipts, deletes = self.exercise()
        self.assertEqual((code, status["result"], receipts, deletes), (0, "PASS", 1, 2))


if __name__ == "__main__":
    unittest.main()
