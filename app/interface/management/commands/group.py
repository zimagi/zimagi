from systems.command.base import command_list
from systems.command import types, mixins, factory


class ChildrenCommand(
    mixins.op.UpdateMixin,
    types.GroupActionCommand
):
    def parse(self):
        self.parse_group_name(help_text = 'parent group name')
        self.parse_group_names(False, help_text = 'one or more child group names')

    def exec(self):
        parent = self.exec_update(self._group, self.group_name)
        for group in self.group_names:
            self.exec_update(self._group, group, { 
                'parent': parent
            })


class Command(types.GroupRouterCommand):

    def get_command_name(self):
        return 'group'

    def get_subcommands(self):
        return command_list(
            factory.ResourceCommands(
                types.GroupActionCommand, 'group',
                list_fields = (
                    ('name', 'Group name'),
                ),
                relations = {
                    'parent': ('group_parent_name', '--parent')
                }
            ),
            ('children', ChildrenCommand)
        )
