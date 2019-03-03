from systems.command import types, factory


class Command(types.NetworkSubnetRouterCommand):

    def get_command_name(self):
        return 'subnet'

    def get_subcommands(self):
        base_name = self.get_command_name()
        return factory.ResourceCommandSet(
            types.NetworkSubnetActionCommand, base_name,
            provider_name = 'network',
            provider_subtype = base_name
        )
