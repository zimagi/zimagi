from systems.command import types, factory


class Command(
    types.LogRouterCommand
):
    def get_command_name(self):
        return 'log'

    def get_subcommands(self):
        parent = types.LogActionCommand
        base_name = self.get_command_name()
        return (
            ('list', factory.ListCommand(parent, base_name)),
            ('get', factory.GetCommand(parent, base_name))
        )
