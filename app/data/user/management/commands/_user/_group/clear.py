from systems.command import types, mixins


class ClearCommand(
    mixins.op.ClearMixin,
    types.UserGroupActionCommand
):
    def parse(self):
        self.parse_user_name(True)

    def confirm(self):
        self.confirmation()       

    def exec(self):
        if self.user_name:
            self.exec_clear_related(self._user_group, self.user, 'groups')
        else:
            for user in self._user.all():
                self.exec_clear_related(self._user_group, user, 'groups')
            
            self.exec_clear(self._user_group)
