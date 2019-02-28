from systems.command import types, factory


class Command(types.NetworkRouterCommand):

    def get_command_name(self):
        return 'subnet'

    def get_subcommands(self):
        return factory.ResourceCommandSet(
            types.NetworkSubnetActionCommand, 'subnet',
            provider_name = 'network',
            provider_subtype = 'subnet',
            list_fields = (
                ('name', 'Name'),
                ('network__name', 'Network'),
                ('network__type', 'Network type'),
                ('cidr', 'CIDR')
            ), 
            relations = {
                'server': 'servers', 
                'mount': 'mounts'
            },
            scopes = {
                'network': '--network'
            }
        )
