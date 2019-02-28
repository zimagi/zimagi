from systems.command import types, factory


class Command(types.NetworkRouterCommand):

    def get_command_name(self):
        return 'network'

    def get_subcommands(self):
        return factory.ResourceCommandSet(
            types.NetworkActionCommand, 'network',
            provider_subtype = 'network',
            list_fields = (
                ('name', 'Name'),
                ('type', 'Type'),
                ('cidr', 'CIDR')
            ), 
            relations = {
                'subnet': 'subnets', 
                'firewall': 'firewalls', 
                'storage': 'storage'
            }
        )
