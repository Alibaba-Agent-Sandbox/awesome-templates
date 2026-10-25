"""Current public launch/native preparation parser contracts; no cloud mutation."""
import os
import shlex
import subprocess
import tempfile
import unittest

class ExpressCliContract(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('ABX'), 'ABX executable required; CI installs the published CLI')
    def test_actual_current_launch_native_prepare_and_cleanup_help(self):
        with tempfile.TemporaryDirectory() as home:
            env = {key: os.environ[key] for key in ('PATH', 'ABX') if key in os.environ}
            env.update(HOME=home, USERPROFILE=home, NO_COLOR='1')
            def help_for(args):
                result = subprocess.run(shlex.split(env['ABX']) + args + ['--help'], env=env,
                    cwd=home, capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                return result.stdout
            public = help_for(['--provider', 'alicloud-express', 'template', 'launch'])
            for flag in ('--alias', '--sandbox-timeout', '--timeout'):
                self.assertIn(flag, public)
            self.assertNotIn('--workflow', public)
            self.assertNotIn('--sandbox-create', public)
            native = ['--native', '--provider', 'alicloud-express', 'template']
            prepare = help_for([*native, 'deploy'])
            for flag in ('--build', '--alias', '--generation', '--start-cmd', '--ready-cmd'):
                self.assertIn(flag, prepare)
            self.assertIn('--yes', help_for([*native, 'delete']))
            from_image = help_for([*native, 'from-image'])
            for flag in ('--registry-username', '--registry-password', '--generation'):
                self.assertIn(flag, from_image)

if __name__ == '__main__': unittest.main()
