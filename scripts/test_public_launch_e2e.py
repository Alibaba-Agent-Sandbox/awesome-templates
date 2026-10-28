import tempfile
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from public_launch_e2e import export_owned_image, installation_provenance, CLI, CLIError, CheckFailed, safe_failure_label, controller_label, cli_diagnostics, safe_diagnostics, application_headers, command_url, load_plan, matches, source_names, cleanup_prepared, cleanup_before_close, delete_sandbox


class PublicLaunchTests(unittest.TestCase):
    def test_real_usage_requires_controller_before_cloud_operations(self):
        import subprocess
        import sys
        result = subprocess.run([sys.executable, str(Path(__file__).with_name('public_launch_e2e.py')),
                                 '--real-usage'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('--real-usage requires --application-controller', result.stderr)

    def test_candidate_source_never_claims_published_package_acceptance(self):
        env = {'PUBLIC_CLI_VERSION': '0.4.17', 'PUBLIC_LAUNCH_DISTRIBUTION': 'source',
               'PUBLIC_LAUNCH_CLI_REF': 'a' * 40, 'PUBLIC_LAUNCH_SDK_REF': 'b' * 40,
               'PUBLIC_LAUNCH_PROVIDERS_REF': 'c' * 40, 'PUBLIC_LAUNCH_TEMPLATES_REF': 'd' * 40}
        source = installation_provenance(env, '0.3.1a5', '0.3.1a5')
        self.assertEqual(source['distribution'], 'source')
        self.assertNotIn('registry', source['cli'])
        self.assertNotIn('registry', source['python_client'])
        self.assertEqual(source['template_source_ref'], 'd' * 40)
        env['PUBLIC_LAUNCH_DISTRIBUTION'] = 'published'
        published = installation_provenance(env, '0.3.1a5', '0.3.1a5')
        self.assertEqual(published['cli']['registry'], 'https://registry.npmjs.org')
        self.assertEqual(published['python_server']['registry'], 'https://pypi.org/simple')
        env['PUBLIC_LAUNCH_DISTRIBUTION'] = 'unknown'
        with self.assertRaises(ValueError):
            installation_provenance(env, '0.3.1a5', '0.3.1a5')

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

    def test_existing_application_token_headers_and_negative_auth(self):
        gateway = {'X-Gateway-Token': 'gateway-value'}
        self.assertEqual(application_headers(gateway, 'app-token'), {
            'X-Gateway-Token': 'gateway-value', 'Authorization': 'Bearer app-token', 'X-Access-Token': 'app-token'})
        wrong = application_headers(gateway, 'intentionally-wrong')
        self.assertEqual(wrong['X-Access-Token'], 'intentionally-wrong')
        self.assertEqual(wrong['Authorization'], 'Bearer intentionally-wrong')
        self.assertEqual(gateway, {'X-Gateway-Token': 'gateway-value'})

    def test_gateway_access_token_is_preserved_case_insensitively(self):
        headers = application_headers({'x-ACCESS-token': 'gateway-credential'}, 'app-token')
        self.assertEqual(headers['x-ACCESS-token'], 'gateway-credential')
        self.assertNotIn('X-Access-Token', headers)

    def test_negative_auth_keeps_gateway_access_token(self):
        gateway = {'x-ACCESS-token': 'gateway-credential'}
        headers = application_headers(gateway, 'intentionally-wrong')
        self.assertEqual(headers['x-ACCESS-token'], 'gateway-credential')
        self.assertEqual(headers['Authorization'], 'Bearer intentionally-wrong')
        self.assertNotIn('X-Access-Token', headers)
        self.assertEqual(gateway, {'x-ACCESS-token': 'gateway-credential'})

    def test_gateway_authorization_is_never_overwritten(self):
        with self.assertRaisesRegex(AssertionError, 'must not overwrite'):
            application_headers({'authorization': 'gateway-credential'}, 'app-token')

    def test_only_owned_failure_labels_are_exported(self):
        for failure in (AssertionError('PRIVATE-ID secret-value'), RuntimeError('CLI secret-value')):
            self.assertIsNone(safe_failure_label(failure))
        self.assertEqual(safe_failure_label(CheckFailed('SDK exec result')), 'SDK exec result')
        self.assertEqual(safe_failure_label(CLIError('template', 2, 'PRIVATE-ID')), 'CLI template failed (exit 2)')

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

    def test_controller_failure_labels_do_not_import_retired_runner_or_expose_secrets(self):
        label = controller_label('[FAIL] fixture-value https://host.invalid/private /tmp/private 1234567890abcdef', ['fixture-value'])
        self.assertEqual(label, '[FAIL] [FIXTURE] [LOCATION] [LOCATION] [ID]')
        self.assertEqual(len(controller_label('x' * 500)), 300)

    def test_resource_journal_uses_the_cli_home_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            cli=CLI('installed-abx','opensandbox',{'HOME':directory})
            self.assertEqual(cli.journal_directory,Path(directory)/'.abx'/'resource-journal')

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

    async def test_stable_not_found_code_still_requires_independent_readback(self):
        class NotFound(Exception):
            pass
        class EngineError(Exception):
            code = 'E2009'
        events = []
        class API:
            @staticmethod
            async def kill_by_id(sid, **kwargs):
                events.append('delete')
                raise EngineError()
            @staticmethod
            async def get_info_by_id(sid, **kwargs):
                events.append('get')
                if events.count('get') == 2:
                    raise EngineError()
        await delete_sandbox(API, 'owned', 'opensandbox', NotFound, delay=0)
        self.assertEqual(events, ['delete', 'get', 'get'])

    async def test_other_error_codes_never_establish_cleanup(self):
        class NotFound(Exception):
            pass
        class EngineError(Exception):
            code = 'E5000'
        class API:
            @staticmethod
            async def kill_by_id(sid, **kwargs):
                return None
            @staticmethod
            async def get_info_by_id(sid, **kwargs):
                raise EngineError()
        with self.assertRaises(EngineError):
            await delete_sandbox(API, 'owned', 'opensandbox', NotFound, delay=0)

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
        from subprocess import CompletedProcess
        class FakeCLI:
            provider = 'alicloud-express'
        tag = 'public-e2e-123-build'
        reference = 'registry.cn-hangzhou.aliyuncs.com/test-namespace/python-hello:' + tag
        entries = [{'intent_id': 'image-one', 'kind': 'image', 'state': 'retained',
                    'id': reference, 'correlation_key': reference}]
        with patch.dict('os.environ', {'ACR_NAMESPACE': 'test-namespace', 'ALIBABA_CLOUD_REGION_ID': 'cn-hangzhou'}), \
             patch('canonical_express_review.delete_absent') as delete, \
             patch('public_launch_e2e.subprocess.run', side_effect=[
                 CompletedProcess([], 0, '', ''),
                 CompletedProcess([], 1, '', 'Error: No such image: ' + reference),
             ]) as docker:
            done, failures = await cleanup_prepared(entries, FakeCLI(), 'public-e2e-123')
        self.assertEqual(done, {'image-one'})
        self.assertEqual(failures, 0)
        delete.assert_called_once_with('/repos/test-namespace/python-hello/tags/' + tag)
        self.assertEqual([call.args[0] for call in docker.call_args_list], [
            ['docker', 'image', 'rm', reference],
            ['docker', 'image', 'inspect', reference],
        ])

    async def test_express_local_push_tag_must_be_independently_absent(self):
        from subprocess import CompletedProcess
        class FakeCLI:
            provider = 'alicloud-express'
        reference = 'registry.cn-hangzhou.aliyuncs.com/test-namespace/python-hello:public-e2e-123-build'
        entries = [{'intent_id': 'image-one', 'kind': 'image', 'state': 'retained',
                    'id': reference, 'correlation_key': reference}]
        for removal, inspection in [
            (CompletedProcess([], 1, '', 'image is in use'), None),
            (CompletedProcess([], 0, '', ''), CompletedProcess([], 0, '[{}]', '')),
        ]:
            with self.subTest(removal_exit=removal.returncode), \
                 patch.dict('os.environ', {'ACR_NAMESPACE': 'test-namespace', 'ALIBABA_CLOUD_REGION_ID': 'cn-hangzhou'}), \
                 patch('canonical_express_review.delete_absent'), \
                 patch('public_launch_e2e.subprocess.run', side_effect=[removal, inspection]) as docker:
                done, failures = await cleanup_prepared(entries, FakeCLI(), 'public-e2e-123')
            self.assertEqual((done, failures), (set(), 1))
            self.assertEqual(docker.call_args_list[0].args[0], ['docker', 'image', 'rm', reference])

    async def test_express_already_absent_local_push_tag_is_reconciled(self):
        from subprocess import CompletedProcess
        class FakeCLI:
            provider = 'alicloud-express'
        reference = 'registry.cn-hangzhou.aliyuncs.com/test-namespace/python-hello:public-e2e-123-build'
        entries = [{'intent_id': 'image-one', 'kind': 'image', 'state': 'retained',
                    'id': reference, 'correlation_key': reference}]
        absent = CompletedProcess([], 1, '', 'Error response from daemon: No such image: ' + reference)
        with patch.dict('os.environ', {'ACR_NAMESPACE': 'test-namespace', 'ALIBABA_CLOUD_REGION_ID': 'cn-hangzhou'}), \
             patch('canonical_express_review.delete_absent'), \
             patch('public_launch_e2e.subprocess.run', side_effect=[absent, absent]) as docker:
            done, failures = await cleanup_prepared(entries, FakeCLI(), 'public-e2e-123')
        self.assertEqual((done, failures), ({'image-one'}, 0))
        self.assertEqual(docker.call_count, 2)

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




    async def test_already_absent_local_image_still_requires_independent_absence(self):
        from subprocess import CompletedProcess
        class FakeCLI:
            provider = 'alicloud-express'
        tag = 'owned:public-e2e-123-build'
        entries = [{'intent_id':'local', 'kind':'image', 'state':'retained',
                    'id':tag, 'correlation_key':tag}]
        missing = CompletedProcess([], 1, '', 'Error: No such image: '+tag)
        for removal, inspection, expected in [
            (missing, missing, True),
            (missing, CompletedProcess([], 0, '[{}]', ''), False),
            (missing, CompletedProcess([], 1, '', 'daemon unavailable'), False),
            (CompletedProcess([], 1, '', 'image in use'), None, False),
        ]:
            with self.subTest(expected=expected, inspection=getattr(inspection, 'returncode', None)), \
                 patch('public_launch_e2e.subprocess.run', side_effect=[removal, inspection]):
                done, failures = await cleanup_prepared(entries, FakeCLI(), 'public-e2e-123')
            self.assertEqual((done, failures), ({'local'},0) if expected else (set(),1))

    async def test_local_alias_in_repository_does_not_own_foreign_tag(self):
        class FakeCLI:
            provider = 'alicloud-express'
        tag='public-e2e-123-build:foreign'
        entries=[{'intent_id':'local','kind':'image','state':'retained','id':tag,'correlation_key':tag}]
        with patch('public_launch_e2e.subprocess.run') as docker:
            self.assertEqual(await cleanup_prepared(entries,FakeCLI(),'public-e2e-123'),(set(),1))
        docker.assert_not_called()


class ImageExportTests(unittest.TestCase):
    def test_foreign_or_ambiguous_images_are_never_exported(self):
        from subprocess import CompletedProcess
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'export'
            with patch('public_launch_e2e.subprocess.run') as run:
                with self.assertRaisesRegex(CheckFailed, 'exactly one owned'):
                    export_owned_image([{'kind': 'image', 'correlation_key': 'foreign-build'}],
                                       'public-e2e-owned', Path(temp) / 'python-hello', target, {})
                run.assert_not_called()
            entries = [{'kind': 'image', 'correlation_key': 'public-e2e-owned-' + x} for x in ('one', 'two')]
            results = [CompletedProcess([], 0, 'sha256:' + x * 64, '') for x in ('a', 'b')]
            with patch('public_launch_e2e.subprocess.run', side_effect=results) as run:
                with self.assertRaisesRegex(CheckFailed, 'exactly one owned'):
                    export_owned_image(entries, 'public-e2e-owned', Path(temp) / 'python-hello', target, {})
                self.assertTrue(all(call.args[0][1:3] == ['image', 'inspect'] for call in run.call_args_list))
            self.assertFalse(target.exists())


def test_foreign_managed_identity_has_controlled_compatibility_diagnostic():
    assert cli_diagnostics(json.dumps({'code':'E8002', 'message':'Template cannot launch on this provider: provider-mismatch.'})) == {'code':'E8002','category':'provider-mismatch'}


class CliIoTests(unittest.IsolatedAsyncioTestCase):
    async def exercise(self, directory, *, corrupt=False, failed_upload=False,
                       ci=False, exec_exit=0, exec_stdout='42\n', provider='opensandbox'):
        from types import SimpleNamespace
        from public_launch_e2e import verify_cli_io
        remote = {};calls = []
        class Files:
            async def read(self, path):return remote[path].decode('utf-8')
            async def exists(self, path):return path in remote
            async def remove(self, path):del remote[path]
        class Adapter:
            def run(self, args, json_output=True, **kwargs):
                calls.append(args)
                if args[0] == 'exec':
                    if self.provider == 'alicloud-express':
                        if json_output:raise CLIError('exec',1,"error: unknown option '--json'")
                        if exec_exit:raise CLIError('exec',exec_exit,'')
                        return exec_stdout.strip()
                    result={'stdout':exec_stdout,'stderr':'','exit_code':exec_exit}
                    return result if json_output else (json.dumps(result) if ci else exec_stdout.strip())
                if args[0] == 'upload':
                    remote[args[3]] = Path(args[2]).read_bytes()
                    if failed_upload:raise RuntimeError('controlled partial upload failure')
                elif args[0] == 'download':
                    Path(args[3]).write_bytes(b'wrong' if corrupt else remote[args[2]])
                elif args[:3] == ['sandbox','files','rm']:
                    del remote[args[args.index('--path')+1]]
                elif args[:3] != ['sandbox','files','stat']:
                    raise AssertionError('unexpected current CLI operation')
        sandbox=SimpleNamespace(id='owned-fixture',files=Files())
        caller=Adapter();caller.provider=provider
        try:
            await verify_cli_io(caller, sandbox, 'owned-run', directory)
        finally:
            self.assertEqual(remote,{})
            self.assertEqual(list(directory.iterdir()),[])
        return calls

    async def test_current_cli_roundtrip_independently_reads_same_unicode_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            calls=await self.exercise(Path(directory))
        self.assertEqual([args[0] for args in calls],['exec','upload','sandbox','download','sandbox'])
        self.assertEqual(calls[0],['exec','owned-fixture','--','python3','-c','print(21 * 2)'])
        self.assertTrue(calls[1][3].startswith('/tmp/owned-run-cli-'))

    async def test_changed_download_bytes_fail_and_owned_file_is_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(CheckFailed,'CLI download preserves'):
                await self.exercise(Path(directory),corrupt=True)

    async def test_ci_automatic_json_does_not_change_exec_or_file_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            await self.exercise(Path(directory),ci=True)

    async def test_express_standard_exec_retains_text_route_in_ci(self):
        with tempfile.TemporaryDirectory() as directory:
            await self.exercise(Path(directory),ci=True,provider='alicloud-express')

    async def test_express_standard_exec_rejects_failed_process(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(CLIError):
                await self.exercise(Path(directory),ci=True,exec_exit=1,provider='alicloud-express')

    async def test_nonzero_exec_cannot_pass_with_expected_stdout(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(CheckFailed,'CLI exec'):
                await self.exercise(Path(directory),ci=True,exec_exit=1)

    async def test_wrong_exec_stdout_cannot_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(CheckFailed,'CLI exec'):
                await self.exercise(Path(directory),ci=True,exec_stdout='43\n')

    async def test_partial_upload_failure_keeps_failure_and_sdk_cleans_owned_file(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError,'partial upload'):
                await self.exercise(Path(directory),failed_upload=True)

class PythonCompatibilityProofTests(unittest.IsolatedAsyncioTestCase):
    async def exercise(self, *, stale_http=False):
        import httpx
        import subprocess
        from types import SimpleNamespace
        from public_launch_e2e import verify_python_compatibility
        files = {}
        programs = []
        class Files:
            async def exists(self, path): return path in files
            async def write(self, path, value): files[path] = value
            async def read(self, path): return files[path]
            async def remove(self, path): del files[path]
        def execute():
            source = next(iter(files.values()))
            programs.append(source)
            result = subprocess.run([__import__('sys').executable, '-I', '-c', source], capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 0)
            return result.stdout
        class Commands:
            async def run(self, name, **kwargs):
                self_case.assertEqual(name, 'run')
                return execute()
        self_case = self
        def cli_run(args):
            self.assertEqual(args[:3], ['run', 'owned-sandbox', 'run'])
            return {'result': execute()}
        def http(request):
            self.assertEqual(request.url.path, '/owned/proxy/9000/commands/run')
            self.assertEqual(request.url.query, b'fixed=1')
            value = 'stale output\n' if stale_http else execute()
            return httpx.Response(200, json={'result': value})
        original = httpx.AsyncClient
        def client(*args, **kwargs):
            kwargs['transport'] = httpx.MockTransport(http)
            return original(*args, **kwargs)
        try:
            with patch('httpx.AsyncClient', side_effect=client):
                await verify_python_compatibility(SimpleNamespace(run=cli_run),
                    SimpleNamespace(id='owned-sandbox', files=Files()),
                    SimpleNamespace(commands=Commands()),
                    'http://provider.invalid/owned/proxy/9000?fixed=1', {}, '/home/user/app')
        finally:
            self.assertEqual(files, {}, 'owned program is absent even when a consumer fails')
        self.assertEqual(len(programs), 3)
        self.assertEqual(len(set(programs)), 3)

    async def test_all_consumers_execute_fresh_real_python_and_cleanup(self):
        await self.exercise()

    async def test_stale_consumer_result_fails_and_still_cleans_owned_program(self):
        with self.assertRaises(CheckFailed):
            await self.exercise(stale_http=True)

if __name__ == '__main__':
    unittest.main()
