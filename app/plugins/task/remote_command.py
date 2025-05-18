from systems.plugins.index import BaseProvider


class Provider(BaseProvider("task", "remote_command")):
    def execute(self, results, params):
        env = self._env_vars(params)
        options = self._merge_options(self.field_options, params, self.field_lock)
        command = self._interpolate(self.field_command, options)

        self._ssh_exec(command, env=env, sudo=self.field_sudo)
