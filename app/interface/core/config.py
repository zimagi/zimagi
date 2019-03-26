from systems.command.base import command_list
from systems.command.factory import resource
from systems.command.types import config


class Command(config.ConfigRouterCommand):

    def get_subcommands(self):
        return command_list(
            resource.ResourceCommandSet(
                config.ConfigActionCommand, self.name,
                provider_name = self.name,
                save_fields = {
                    'value_type': ('config_value_type', '--type'),
                    'value': ('config_value', True)
                }
            )
        )
