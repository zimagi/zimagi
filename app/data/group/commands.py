from settings.roles import Roles
from base.command.base import command_set
from base.command.router import RouterCommand
from base.command.action import ActionCommand
from systems.command.factory import resource



class GroupRouterCommand(RouterCommand):

    def get_priority(self):
        return 80


class GroupActionCommand(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.user_admin,
            Roles.config_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 80


class ChildrenCommand(
    GroupActionCommand
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


class Command(GroupRouterCommand):

    def get_subcommands(self):
        return command_set(
            resource.ResourceCommandSet(
                GroupActionCommand, self.name,
                provider_name = self.name
            ),
            ('children', ChildrenCommand)
        )
