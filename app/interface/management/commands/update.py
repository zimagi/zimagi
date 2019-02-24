from systems.command import types, mixins


class Command(
    mixins.op.UpdateMixin,
    types.EnvironmentActionCommand
):
    def get_command_name(self):
        return 'update'

    def parse(self):
        self.parse_env_fields()

    def exec(self):
        environment = self.get_env()
        self.exec_update(self._env, environment.name, self.env_fields)
