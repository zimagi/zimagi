from systems.command import types, mixins


class GetCommand(
    mixins.op.GetMixin,
    types.ConfigActionCommand
):
    def groups_allowed(self):
        return False # Configuration model access

    def parse(self):
        self.parse_config_name()

    def exec(self):
        self.exec_get(self._config, self.config_name)
