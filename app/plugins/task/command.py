from .base import BaseProvider
from .mixins import cli

import re
import shlex


class Provider(
    cli.CLITaskMixin,
    BaseProvider
):
    def get_fields(self):
        return {
            'command': '<required>',
            'env': {},
            'input': None,
            'cwd': None,
            'display': True,
            'sudo': False,
            'lock': False,
            'options': {}
        }

    def execute(self, results, params):
        if 'command' in self.config:
            command = self.config['command']
        else:
            self.command.error("Command task provider must have a 'command' property specified")

        env = self._env_vars(params)
        stdin = params.pop('input', self.config.get('input', None))
        cwd = params.pop('cwd', self.config.get('cwd', None))
        display = params.pop('display', self.config.get('display', True))
        sudo = self.config.get('sudo', False)
        lock = self.config.get('lock', False)
        options = self._merge_options(self.config.get('options', {}), params, lock)

        command = self._interpolate(command, options)
        if sudo:
            command = 'sudo ' + command[0]
        else:
            command = command[0]

        self.command.sh(shlex.split(command),
            input = stdin,
            display = display,
            env = env,
            cwd = cwd
        )
