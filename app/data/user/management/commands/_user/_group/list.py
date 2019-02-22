from systems.command import types, mixins


class ListCommand(
    mixins.op.ListMixin,
    types.UserGroupActionCommand
):
    def parse(self):
        self.parse_user_name(True)

    def exec(self):
        fields = [('name', 'Group')]

        if self.user_name:
            self.user # Validate user
            self.exec_list_related(self._user, self.user_name, 'groups', *fields)
        else:
            self.exec_list(self._user_group, *fields)
