from systems.command.base import command_list
from systems.command import types, mixins, factory


class ChildrenCommand(
    types.GroupActionCommand
):
    def parse(self):
        self.parse_group_name(help_text = 'parent group name')
        self.parse_group_names(False, help_text = 'one or more child group names')

    def exec(self):
        parent, created = self._group.store(self.group_name)
        for group in self.group_names:
            self._group.store(group, parent = parent)


class Command(types.GroupRouterCommand):

    def get_command_name(self):
        return 'group'

    def get_subcommands(self):
        base_name = self.get_command_name()
        return command_list(
            factory.ResourceCommandSet(
                types.GroupActionCommand, base_name,
                provider_name = base_name
            ),
            ('children', ChildrenCommand)
        )
