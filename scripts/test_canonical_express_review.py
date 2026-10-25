"""Read-only authorization and current shared owned-registry cleanup guards."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import canonical_express_review as review

APPROVAL = {"REVIEW_ENABLE": "approved", "REVIEW_HEAD": "a" * 40,
            "REVIEW_APPROVED_SHA": "a" * 40, "REVIEW_SAME_REPOSITORY": "true"}


class AuthorizationTest(unittest.TestCase):
    def test_disabled_wrong_head_and_fork_stay_blocked(self):
        self.assertTrue(review.authorization(APPROVAL)[0])
        for changes in ({"REVIEW_ENABLE": ""}, {"REVIEW_APPROVED_SHA": "b" * 40},
                        {"REVIEW_SAME_REPOSITORY": "false"}, {"REVIEW_HEAD": ""}):
            with self.subTest(changes=changes):
                self.assertFalse(review.authorization(APPROVAL | changes)[0])
        self.assertEqual(review.authorization({})[1], ["python-hello"])

    def test_current_catalog_scope_and_invalid_input(self):
        self.assertEqual(review.select("python-hello,pi"), ["python-hello", "pi"])
        self.assertEqual(len(review.select("all")), 46)
        for value in ("", "../python-hello", "python-hello,python-hello", "python-hello;echo bad", "base"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                review.select(value)

    def test_planning_never_executes_cloud_or_exposes_environment_values(self):
        for environment in ({}, APPROVAL, APPROVAL | {"ABX_SANDBOX_API_KEY": "synthetic-private-key"}):
            with self.subTest(environment=bool(environment)), tempfile.TemporaryDirectory() as directory:
                old = Path.cwd()
                try:
                    os.chdir(directory)
                    env = environment | {"GITHUB_OUTPUT": str(Path(directory) / "output")}
                    with patch.dict(os.environ, env, clear=True), patch.object(review.urllib.request, 'urlopen') as network:
                        self.assertEqual(review.plan(), 0)
                        network.assert_not_called()
                    text = Path('canonical-authorization.json').read_text()
                    receipt = json.loads(text)
                    self.assertFalse(receipt['cloud_executed'])
                    self.assertEqual(receipt['entry_point'], 'public-template-launch.yml')
                    self.assertNotIn('synthetic-private-key', text)
                finally:
                    os.chdir(old)


class RegistryCleanupTest(unittest.TestCase):
    def test_existing_current_helper_deletes_then_independently_checks_absence(self):
        calls = []
        def request(method, path):
            calls.append((method, path))
            if method == 'GET':
                raise FileNotFoundError
        with patch.object(review, 'registry', side_effect=request):
            review.delete_absent('/owned-fixture')
        self.assertEqual(calls, [('DELETE', '/owned-fixture'), ('GET', '/owned-fixture')])

    def test_already_absent_still_receives_independent_readback(self):
        with patch.object(review, 'registry', side_effect=FileNotFoundError) as request:
            review.delete_absent('/owned-fixture')
        self.assertEqual(request.call_count, 2)

    def test_unconfirmed_deletion_is_a_failure(self):
        with patch.object(review, 'registry'), patch.object(review.time, 'sleep'):
            with self.assertRaisesRegex(RuntimeError, 'not confirmed'):
                review.delete_absent('/owned-fixture')


if __name__ == '__main__':
    unittest.main()
