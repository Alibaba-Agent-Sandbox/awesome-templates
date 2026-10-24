import tempfile
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from public_launch_e2e import CLI, CLIError, cli_diagnostics, safe_diagnostics, command_url, load_plan, matches, source_names, cleanup_prepared, cleanup_before_close, delete_sandbox


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


    def test_cli_diagnostics_only_exports_controlled_values(self):
        payload = json.dumps({'code': 'E8003', 'message': 'Template startup failed; owned sandbox PRIVATE-ID; HTTP 401 secret-value',
                              'suggestion': 'secret-value', 'private': 'PRIVATE-ID'})
        self.assertEqual(cli_diagnostics(payload), {'code': 'E8003', 'category': 'template-startup', 'http_status': 401})
        failure = CLIError('template', 2, payload)
        self.assertNotIn('PRIVATE-ID', str(failure))
        self.assertNotIn('secret-value', json.dumps(safe_diagnostics(failure)))
        self.assertEqual(cli_diagnostics(json.dumps({'code': 'private-token', 'message': 'unrecognized secret-value'})), {})

    def test_native_selection_is_the_first_cli_argument(self):
        from subprocess import CompletedProcess
        with patch('public_launch_e2e.subprocess.run', return_value=CompletedProcess([], 0, '[]', '')) as run:
            CLI('node /tmp/installed-abx.js', 'alicloud-express', {}).run(['template', 'list'], native=True)
        self.assertEqual(run.call_args.args[0], ['node', '/tmp/installed-abx.js', '--native', '--provider', 'alicloud-express', '--json', 'template', 'list'])



class CleanupTests(unittest.IsolatedAsyncioTestCase):
    async def test_client_close_failure_does_not_skip_resource_cleanup(self):
        events = []
        async def release():
            events.extend(['sandbox deleted', 'template deleted', 'image deleted'])
        class Client:
            async def aclose(self):
                events.append('application close')
                raise RuntimeError('local HTTP close failure')
        class Sandbox:
            async def close(self):
                events.append('sandbox close')
        self.assertEqual(await cleanup_before_close(release, Client(), Sandbox()), ['RuntimeError'])
        self.assertEqual(events, ['sandbox deleted', 'template deleted', 'image deleted', 'application close', 'sandbox close'])

    async def test_delete_polls_control_plane_without_reconnect(self):
        class NotFound(Exception):
            pass
        events = []
        class API:
            @staticmethod
            async def kill_by_id(sid, **kwargs):
                events.append('delete')
            @staticmethod
            async def get_info_by_id(sid, **kwargs):
                events.append('get')
                if events.count('get') == 3:
                    raise NotFound()
        await delete_sandbox(API, 'owned', 'opensandbox', NotFound, delay=0)
        self.assertEqual(events, ['delete', 'get', 'get', 'get'])

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
                calls.append((args, kwargs))
                return [{'templateID': 'owned-template'}] if args[1] == 'list' else ''
        entries = [{'intent_id': 'one', 'kind': 'template', 'state': 'retained', 'id': 'owned-template',
                    'correlation_key': 'public-e2e-123-build'}]
        done, failures = await cleanup_prepared(entries, FakeCLI(), 'public-e2e-123')
        self.assertEqual(done, set())
        self.assertEqual(failures, 1)
        self.assertEqual([item[0][1] for item in calls], ['delete', 'list'])
        self.assertTrue(all(item[1].get('native') is True for item in calls))
        self.assertEqual(calls[-1][0], ['template', 'list'])

    async def test_cleanup_diagnostic_never_contains_resource_identifier(self):
        class FakeCLI:
            provider = 'alicloud-express'
            def run(self, args, **kwargs):
                raise CLIError('template', 2, json.dumps({'code': 'E8003', 'message': 'PRIVATE-ID secret-value HTTP 403'}))
        entries = [{'intent_id': 'one', 'kind': 'template', 'state': 'retained', 'id': 'PRIVATE-ID',
                    'correlation_key': 'public-e2e-123-build'}]
        details = []
        done, failures = await cleanup_prepared(entries, FakeCLI(), 'public-e2e-123', details)
        self.assertEqual((done, failures), (set(), 1))
        self.assertEqual(details, [{'kind': 'template', 'failure_type': 'CLIError', 'code': 'E8003', 'http_status': 403}])
        self.assertNotIn('PRIVATE-ID', json.dumps(details))

    async def test_express_shared_repository_deletes_only_owned_journal_tag(self):
        class FakeCLI:
            provider = 'alicloud-express'
        tag = 'public-e2e-123-build'
        reference = 'registry.cn-hangzhou.aliyuncs.com/test-namespace/python-hello:' + tag
        entries = [{'intent_id': 'image-one', 'kind': 'image', 'state': 'retained',
                    'id': reference, 'correlation_key': reference}]
        with patch.dict('os.environ', {'ACR_NAMESPACE': 'test-namespace', 'ALIBABA_CLOUD_REGION_ID': 'cn-hangzhou'}), \
             patch('canonical_express_review.delete_absent') as delete:
            done, failures = await cleanup_prepared(entries, FakeCLI(), 'public-e2e-123')
        self.assertEqual(done, {'image-one'})
        self.assertEqual(failures, 0)
        delete.assert_called_once_with('/repos/test-namespace/python-hello/tags/' + tag)

    async def test_express_alias_in_repository_does_not_own_foreign_tag(self):
        class FakeCLI:
            provider = 'alicloud-express'
        reference = 'registry.cn-hangzhou.aliyuncs.com/test-namespace/public-e2e-123-build:someone-else'
        entries = [{'intent_id': 'image-one', 'kind': 'image', 'state': 'retained',
                    'id': reference, 'correlation_key': reference}]
        with patch.dict('os.environ', {'ACR_NAMESPACE': 'test-namespace'}), \
             patch('canonical_express_review.delete_absent') as delete:
            done, failures = await cleanup_prepared(entries, FakeCLI(), 'public-e2e-123')
        self.assertEqual(done, set())
        self.assertEqual(failures, 1)
        delete.assert_not_called()

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
