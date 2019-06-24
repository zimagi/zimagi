from systems.command.base import command_set
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
            self._group.store(group,
                provider_type = parent.provider_type,
                parent = parent
            )

        self.success("Successfully saved group {}".format(parent.name))


class Command(group.GroupRouterCommand):

    def get_subcommands(self):
        return command_set(
            resource.ResourceCommandSet(
                group.GroupActionCommand, self.name,
                provider_name = self.name
            ),
            ('children', ChildrenCommand)
        )
