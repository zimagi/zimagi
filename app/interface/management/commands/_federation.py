from systems.command import types, factory


class Command(types.FederationRouterCommand):

    def get_command_name(self):
        return 'federation'

    def get_subcommands(self):
        return factory.ResourceCommandSet(
            types.FederationActionCommand, 'federation',
            list_fields = (
                ('name', 'Name'),
                ('type', 'Type'),
                ('cidr', 'CIDR')
            ),
            relations = {
                'network': 'networks'
            }            
        )
