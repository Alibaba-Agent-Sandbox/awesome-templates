"""Official mini environment extension: bounded actions in the CLI's owned group.

This is an execution adapter, not an OS security boundary. Only use owned fresh
sandboxes and explicitly authorized model-generated shell commands.
"""
import os
import platform
from swe_process import action as run_action
from minisweagent.environments.local import LocalEnvironment


class OwnedLocalEnvironment(LocalEnvironment):
    def execute(self, action, cwd='', *, timeout=None):
        env = {name: os.environ[name] for name in ('HOME', 'LANG', 'LC_ALL') if name in os.environ}
        env.update(self.config.env)
        result = run_action(action.get('command', ''), cwd=cwd or self.config.cwd,
                            env=env, timeout=timeout or self.config.timeout)
        self._check_finished(result)
        return result

    def get_template_vars(self, **kwargs):
        return self.config.model_dump() | platform.uname()._asdict() | kwargs
