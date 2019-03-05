from systems.command import types, factory


class Command(types.StorageRouterCommand):

    def get_command_name(self):
        return 'mount'

    def get_subcommands(self):
        base_name = self.get_command_name()
        return factory.ResourceCommandSet(
            types.StorageMountActionCommand, base_name,
            provider_name = 'storage',
            provider_subtype = base_name
        )
