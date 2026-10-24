import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from public_launch_e2e import CLI, command_url, load_plan, matches, source_names, cleanup_prepared


class PublicLaunchTests(unittest.TestCase):
    def test_all_source_templates_have_named_smoke_cases(self):
        names = source_names()
        self.assertEqual(len(names), 46)
        for name in names:
            source, manifest, cases = load_plan(name)
            self.assertTrue(cases)
            self.assertTrue((source / 'commands.py').is_file())

    def test_native_reference_is_not_accepted_as_source_template(self):
        with self.assertRaises(ValueError):
            load_plan('base')

    def test_results_are_compared_not_only_http_success(self):
        self.assertTrue(matches('42\n', '42'))
        self.assertFalse(matches({'ok': False}, {'ok': True}))
        self.assertFalse(matches('0', 0))
        self.assertFalse(matches('anything', None))

    def test_gateway_prefix_and_query_are_retained(self):
        self.assertEqual(command_url('https://gateway.invalid/sbx/port/9000?tenant=a', 'hello'),
            'https://gateway.invalid/sbx/port/9000/commands/hello?tenant=a')
        self.assertTrue(command_url('https://host.invalid/', '../hello').endswith('/commands/..%2Fhello'))

    def test_endpoint_rejects_user_information_and_non_http(self):
        for endpoint in ['file:///tmp/server', 'https://secret@host.invalid', 'https://host.invalid/#x']:
            with self.assertRaises(ValueError):
                command_url(endpoint, 'hello')

    def test_cli_failure_does_not_leak_raw_output(self):
        from subprocess import CompletedProcess
        with patch('public_launch_e2e.subprocess.run', return_value=CompletedProcess([], 1, 'PRIVATE-ID', 'secret-value')):
            with self.assertRaisesRegex(RuntimeError, '^CLI template failed \\(exit 1\\)$'):
                CLI('node /tmp/installed-abx.js', 'opensandbox', {}).run(['template', 'launch'])


class CleanupTests(unittest.IsolatedAsyncioTestCase):
    async def test_unknown_registry_and_uncertain_intents_are_retained(self):
        entries = [
            {'intent_id': 'one', 'kind': 'image', 'state': 'retained', 'id': 'unfamiliar.invalid/team/image@sha256:' + 'a' * 64,
             'correlation_key': 'unfamiliar.invalid/team/image:public-e2e-123-build'},
            {'intent_id': 'two', 'kind': 'template', 'state': 'uncertain', 'correlation_key': 'public-e2e-123-build'},
        ]
        done, failures = await cleanup_prepared(entries, CLI('abx', 'opensandbox', {}), 'public-e2e-123')
        self.assertEqual(done, set())
        self.assertEqual(failures, 0)

    async def test_template_absence_requires_readback(self):
        calls = []
        class FakeCLI:
            provider = 'alicloud-express'
            def run(self, args, **kwargs):
                calls.append(args)
                return [{'templateID': 'owned-template'}] if args[1] == 'list' else ''
        entries = [{'intent_id': 'one', 'kind': 'template', 'state': 'retained', 'id': 'owned-template',
                    'correlation_key': 'public-e2e-123-build'}]
        done, failures = await cleanup_prepared(entries, FakeCLI(), 'public-e2e-123')
        self.assertEqual(done, set())
        self.assertEqual(failures, 1)
        self.assertEqual([item[1] for item in calls], ['delete', 'list'])

    async def test_foreign_template_is_never_deleted(self):
        class FakeCLI:
            provider = 'alicloud-express'
            def run(self, *args, **kwargs):
                raise AssertionError('foreign resource must not be touched')
        entries = [{'intent_id': 'one', 'kind': 'template', 'state': 'retained', 'id': 'foreign-template',
                    'correlation_key': 'different-run-build'}]
        done, failures = await cleanup_prepared(entries, FakeCLI(), 'public-e2e-123')
        self.assertEqual(done, set())
        self.assertEqual(failures, 0)


if __name__ == '__main__':
    unittest.main()
