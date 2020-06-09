from systems.plugins.index import BaseProvider

import re
import shlex


class Provider(BaseProvider('task', 'command')):

    def execute(self, results, params):
        env = self._env_vars(params)
        stdin = params.pop('input', self.field_input)
        cwd = params.pop('cwd', self.field_cwd)
        display = params.pop('display', self.field_display)
        options = self._merge_options(self.field_options, params, self.field_lock)

        command = self._interpolate(self.field_command, options)
        if self.field_sudo:
            command = 'sudo ' + command[0]
        else:
            command = command[0]

        self.command.sh(shlex.split(command),
            input = stdin,
            display = display,
            env = env,
            cwd = cwd
        )
