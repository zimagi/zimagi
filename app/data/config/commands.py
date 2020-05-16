from settings.roles import Roles
from base.command.base import command_set
from base.command.router import RouterCommand
from base.command.action import ActionCommand
from systems.command.factory import resource


class ConfigRouterCommand(RouterCommand):

    def get_priority(self):
        return 75


class ConfigActionCommand(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.config_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 75


class Command(ConfigRouterCommand):

    def get_subcommands(self):
        return command_set(
            resource.ResourceCommandSet(
                ConfigActionCommand, self.name,
                provider_name = self.name,
                save_fields = {
                    'value_type': ('config_value_type', '--type'),
                    'value': ('config_value', True)
                }
            )
        )
