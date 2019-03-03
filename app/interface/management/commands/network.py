from systems.command import types, factory


class Command(types.NetworkRouterCommand):

    def get_command_name(self):
        return 'network'

    def get_subcommands(self):
        base_name = self.get_command_name()
        return factory.ResourceCommandSet(
            types.NetworkActionCommand, base_name,
            provider_name = base_name,
            provider_subtype = base_name
        )
