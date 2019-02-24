from systems.command import types, mixins


class Command(
    mixins.op.GetMixin,
    types.EnvironmentActionCommand
):
    def get_command_name(self):
        return 'get'

    def exec(self):
        self.exec_get(self._env, self._env.get_env())
