from systems.command import types, mixins


class RemoveCommand(
    mixins.op.RemoveMixin,
    types.ConfigActionCommand
):
    def parse(self):
        self.parse_force()
        self.parse_config_name()

    def confirm(self):
        self.confirmation()       

    def exec(self):
        self.exec_rm(self._config, self.config_name)
