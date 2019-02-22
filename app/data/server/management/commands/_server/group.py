from systems.command import types, mixins


class GroupCommand(
    mixins.op.UpdateMixin,
    types.ServerActionCommand
):
    def parse(self):
        self.parse_server_group(help_text = 'parent server group name')
        self.parse_server_groups(False, help_text = 'one or more child server group names')

    def exec(self):
        parent = self.exec_update(self._server_group, self.server_group_name)

        for group in self.server_group_names:
            self.exec_update(self._server_group, group, { 
                'parent': parent
            })
