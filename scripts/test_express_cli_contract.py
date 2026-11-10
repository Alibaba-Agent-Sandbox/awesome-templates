"""Current public launch/native preparation parser contracts; no cloud mutation."""
import os
import shlex
import subprocess
import tempfile
import unittest

class ExpressCliContract(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('ABX'), 'ABX executable required; use the matching source CLI')
    def test_actual_provider_exec_output_dispatch_without_backend_credentials(self):
        with tempfile.TemporaryDirectory() as home:
            env={key:os.environ[key] for key in ('PATH','ABX') if key in os.environ}
            env.update(HOME=home,USERPROFILE=home,NO_COLOR='1',CI='true',ABX_NO_KEYCHAIN='1')
            def invoke(provider,json_output):
                return subprocess.run(shlex.split(env['ABX'])+['--provider',provider]
                    +(['--json'] if json_output else [])
                    +['sandbox','exec','fixture-not-real','--','python3','-c','print(42)'],
                    env=env,cwd=home,capture_output=True,text=True,timeout=30)
            for provider,json_output in [('alicloud-express',False),('opensandbox',True)]:
                result=invoke(provider,json_output)
                self.assertNotEqual(result.returncode,0)
                self.assertNotIn('unknown option',result.stdout+result.stderr)
                self.assertNotIn('Usage:',result.stdout+result.stderr)

    @unittest.skipUnless(os.environ.get('ABX'), 'ABX executable required; use the matching source CLI')
    def test_actual_current_launch_native_prepare_and_cleanup_help(self):
        with tempfile.TemporaryDirectory() as home:
            env = {key: os.environ[key] for key in ('PATH', 'ABX') if key in os.environ}
            env.update(HOME=home, USERPROFILE=home, NO_COLOR='1')
            def help_for(args):
                result = subprocess.run(shlex.split(env['ABX']) + args + ['--help'], env=env,
                    cwd=home, capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                return result.stdout
            public = help_for(['--provider', 'alicloud-express', 'deploy'])
            for flag in ('--name', '--sandbox-timeout', '--build-timeout'):
                self.assertIn(flag, public)
            self.assertNotIn('--workflow', public)
            self.assertNotIn('--sandbox-create', public)
            author = help_for(['template', 'build'])
            for flag in ('--out', '--clean', '--build-profile'):
                self.assertIn(flag, author)
            self.assertIn('--input', help_for(['--provider', 'alicloud-express', 'provider', 'run', 'template.delete']))


if __name__ == '__main__': unittest.main()
