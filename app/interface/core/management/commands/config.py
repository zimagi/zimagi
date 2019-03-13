from systems.command.base import command_list
from systems.command.factory import resource
from systems.command.types import config


class Command(config.ConfigRouterCommand):

    def get_command_name(self):
        return 'config'

    def get_subcommands(self):
        base_name = self.get_command_name()
        return command_list(
            resource.ResourceCommandSet(
                config.ConfigActionCommand, base_name,
                provider_name = base_name,
                save_fields = {
                    'value_type': ('config_value_type', '--type'),
                    'value': ('config_value', True)
                }
            )
        )
