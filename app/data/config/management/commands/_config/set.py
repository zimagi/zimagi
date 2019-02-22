from systems.command import types, mixins


class SetCommand(
    mixins.op.UpdateMixin,
    types.ConfigActionCommand
):
    def parse(self):
        self.parse_config_name()
        self.parse_config_value()

    def exec(self):
        self.exec_update(self._config, self.config_name, {
            'value': self.config_value,
            'user': self.active_user.username if self.active_user else None,
        })
