from systems.command import types, mixins


class AddCommand(
    mixins.op.AddMixin,
    types.UserActionCommand
):
    def parse(self):
        self.parse_user_name()
        self.parse_user_fields()

    def exec(self):
        self.exec_add(self._user, self.user_name, self.user_fields)
