from systems.command import types, mixins


class AddCommand(
    mixins.op.AddMixin,
    types.UserGroupActionCommand
):
    def parse(self):
        self.parse_user_name()
        self.parse_user_groups(False)

    def exec(self):
        self.exec_add_related(
            self._user_group, 
            self.user, 'groups', 
            self.user_group_names
        )
