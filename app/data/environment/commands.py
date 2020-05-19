from settings.roles import Roles
from base.command.base import command_set
from base.command.router import RouterCommand
from base.command.action import ActionCommand
from systems.command.factory import resource


class EnvironmentRouterCommand(RouterCommand):

    def get_priority(self):
        return 100


class EnvironmentActionCommand(ActionCommand):

    def groups_allowed(self):
        return False

    def server_enabled(self):
        return False

    def get_priority(self):
        return 100


class Command(
    EnvironmentRouterCommand
):
    def get_subcommands(self):
        name = 'environment'
        return command_set(
            resource.ResourceCommandSet(
                EnvironmentActionCommand, name,
                provider_name = name,
                name_field = 'curr_env_name',
                rm_post_methods = {
                    'delete_env': None
                },
                allow_list = False,
                allow_clear = False
            )
        )
