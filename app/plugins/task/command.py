from .base import BaseProvider
from .mixins import cli

import re


class Provider(
    cli.CLITaskMixin,
    BaseProvider
):
    def execute(self, results, params):
        if 'command' in self.config:
            command = self.config['command']
        else:
            self.command.error("Command task provider must have a 'command' property specified")

        sudo = self.config.get('sudo', False)
        lock = self.config.get('lock', False)
        options = self._merge_options(self.config.get('options', {}), params, lock)

        command = self._interpolate(command, options)
        if sudo:
            command = 'sudo ' + command[0]
        else:
            command = command[0]

        self.command.sh(re.split(r'\s+', command),
            input = self.config.get('input', None),
            display = self.config.get('display', True),
            env = self.config.get('env', {}),
            cwd = self.config.get('cwd', None)
        )
