from utility.data import ensure_list
from .base import BaseProvider
from .mixins import cli

import os


class Provider(
    cli.CLITaskMixin,
    BaseProvider
):
    def execute(self, results, params):
        if 'script' in self.config:
            script_path = self.get_path(self.config['script'])
        else:
            self.command.error("Script task provider must have a 'script' property specified that links to an executable file")

        if not os.path.exists(script_path):
            self.command.error("Script task provider file {} does not exist".format(script_path))

        sudo = self.config.get('sudo', False)
        lock = self.config.get('lock', False)
        options = self._merge_options(self.config.get('options', {}), params, lock)
        args = ensure_list(self.config.get('args', []))

        command = [script_path] + self._interpolate(args, options)
        if sudo:
            command = ['sudo'] + command

        self.command.sh(command,
            input = self.config.get('input', None),
            display = self.config.get('display', True),
            env = self.config.get('env', {}),
            cwd = self.config.get('cwd', None)
        )
