from systems.command import types, mixins


class RemoveCommand(
    mixins.op.RemoveMixin,
    types.UserActionCommand
):
    def parse(self):
        self.parse_user_name()

    def confirm(self):
        self.confirmation()       

    def exec(self):
        self.exec_rm(self._user, self.user_name)
