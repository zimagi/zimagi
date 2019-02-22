from systems.command import types, mixins


class UpdateCommand(
    mixins.op.UpdateMixin,
    types.UserActionCommand
):
    def parse(self):
        self.parse_user_name()
        self.parse_user_fields()

    def exec(self):
        self.exec_update(self._user, self.user_name, self.user_fields)
