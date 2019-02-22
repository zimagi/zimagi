from systems.command import types, factory


class Command(types.StorageRouterCommand):

    def get_command_name(self):
        return 'storage'

    def get_subcommands(self):
        return factory.ResourceCommands(
            types.StorageActionCommand, 'storage',
            provider_name = 'storage',
            provider_subtype = 'storage',
            list_fields = (
                ('name', 'Name'),
                ('type', 'Type')
            ),
            relations = ('mounts',),
            scopes = {
                'network': '--network'
            }
        )
