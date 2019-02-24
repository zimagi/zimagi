from systems.command import types, factory


class Command(types.StorageRouterCommand):

    def get_command_name(self):
        return 'mount'

    def get_subcommands(self):
        return factory.ResourceCommands(
            types.StorageMountActionCommand, 'mount',
            provider_name = 'storage',
            provider_subtype = 'mount',
            list_fields = (
                ('name', 'Name'),
                ('storage__name', 'Storage'),
                ('storage__type', 'Storage type'),
                ('remote_host', 'Remote host'),
                ('remote_path', 'Remote path')
            ),
            relations = { 
                'firewall': 'firewalls' 
            },
            scopes = {
                'network': '--network',
                'subnet': '--subnet'
            }
        )
