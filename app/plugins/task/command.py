import shlex

from systems.plugins.index import BaseProvider
from utility.shell import ShellError


class Provider(BaseProvider("task", "command")):
    def execute(self, results, params):
        env = self._env_vars(params)
        stdin = params.pop("input", self.field_input)
        cwd = params.pop("cwd", self.field_cwd)
        display = params.pop("display", self.field_display)
        options = self._merge_options(self.field_options, params, self.field_lock)

        command = self._interpolate(self.field_command, options)
        success = self.command.sh(
            shlex.split(command[0]), input=stdin, display=display, env=env, cwd=cwd, sudo=self.field_sudo
        )
        if not success:
            raise ShellError(f"Shell command failed: {command[0]}")
