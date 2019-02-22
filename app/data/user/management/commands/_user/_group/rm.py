from systems.command import types, mixins


class RemoveCommand(
    mixins.op.RemoveMixin,
    types.UserGroupActionCommand
):
    def parse(self):
        self.parse_user_name()
        self.parse_user_groups(False)

    def confirm(self):
        self.confirmation()      

    def exec(self):
        self.exec_rm_related(self._user_group, self.user, 'groups', self.user_group_names)
