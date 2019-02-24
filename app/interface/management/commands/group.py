from systems.command import types, mixins


class Command(
    mixins.op.UpdateMixin,
    types.ServerActionCommand
):
    def get_command_name(self):
        return 'group'

    def parse(self):
        self.parse_group(help_text = 'parent group name')
        self.parse_groups(False, help_text = 'one or more child group names')

    def exec(self):
        parent = self.exec_update(self._group, self.group_name)

        for group in self.group_names:
            self.exec_update(self._group, group, { 
                'parent': parent
            })
