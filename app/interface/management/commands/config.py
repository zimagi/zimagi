from systems.command.base import command_list
from systems.command import types, factory


class Command(types.ConfigRouterCommand):

    def get_command_name(self):
        return 'config'

    def get_subcommands(self):
        return command_list(
            factory.ResourceCommandSet(
                types.ConfigActionCommand, 
                self.get_command_name(),
                save_fields = {
                    'value': ('config_value', True)
                }
            )
        )
