from systems.plugins.index import BaseProvider
from utility.data import ensure_list

import os


class Provider(BaseProvider('task', 'script')):

    def execute(self, results, params):
        script_path = self.get_path(self.field_script)

        if not os.path.exists(script_path):
            self.command.error("Script task provider file {} does not exist".format(script_path))

        env = self._env_vars(params)
        stdin = params.pop('input', self.field_input)
        cwd = params.pop('cwd', self.field_cwd)
        display = params.pop('display', self.field_display)
        options = self._merge_options(self.field_options, params, self.field_lock)

        command = [script_path] + self._interpolate(ensure_list(self.field_args), options)
        self.command.sh(command,
            input = stdin,
            display = display,
            env = env,
            cwd = cwd,
            sudo = self.field_sudo
        )
