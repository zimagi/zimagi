from settings.roles import Roles
from systems.command.base import command_set
from systems.command.factory import resource
from systems.command.types import config
from .router import RouterCommand
from .action import ActionCommand


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


class Command(config.ConfigRouterCommand):

    def get_subcommands(self):
        return command_set(
            resource.ResourceCommandSet(
                config.ConfigActionCommand, self.name,
                provider_name = self.name,
                save_fields = {
                    'value_type': ('config_value_type', '--type'),
                    'value': ('config_value', True)
                }
            )
        )
