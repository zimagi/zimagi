from systems.command.base import command_list
from systems.command.factory import resource
from systems.command.types import group


class ChildrenCommand(
    group.GroupActionCommand
):
    def parse(self):
        self.parse_group_name(help_text = 'parent group name')
        self.parse_group_names(False, help_text = 'one or more child group names')

    def exec(self):
        self.exec_local('group save', {
            'group_name': self.group_name,
            'verbosity': 0
        })
        parent = self._group.retrieve(self.group_name)
        for group in self.group_names:
            self._group.store(group, parent = parent)

        self.success("Successfully saved group {}".format(parent.name))


class Command(group.GroupRouterCommand):

    def get_command_name(self):
        return 'group'

    def get_subcommands(self):
        base_name = self.get_command_name()
        return command_list(
            resource.ResourceCommandSet(
                group.GroupActionCommand, base_name,
                provider_name = base_name
            ),
            ('children', ChildrenCommand)
        )
