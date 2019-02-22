from systems.command import types, mixins


class Command(
    mixins.op.ListMixin,
    types.EnvironmentActionCommand
):
    def get_command_name(self):
        return 'list'

    def exec(self):
        self.exec_list(self._env,
            ('name', 'Name'),
            ('host', 'Host'),
            ('port', 'Port'),
            ('token', 'Token'),
            ('repo', 'Registry'),
            ('image', 'Image')
        )
