from systems.command.base import command_list
from systems.command import types, factory


class Command(types.NetworkRouterCommand):

    def get_command_name(self):
        return 'firewall'

    def get_subcommands(self):
        return command_list(
            factory.ResourceCommands(
                types.NetworkFirewallActionCommand, 'firewall',
                provider_name = 'network',
                provider_subtype = 'firewall',
                list_fields = (
                    ('name', 'Name'),
                    ('network__name', 'Network'),
                    ('network__type', 'Network type')
                ), 
                relations = {
                    'rule': 'rules'
                },
                scopes = {
                    'network': '--network'
                }
            ),
            ('rule', factory.Router(
                types.NetworkRouterCommand,
                factory.ResourceCommands(
                    types.NetworkFirewallActionCommand, 'firewall_rule',
                    provider_name = 'network',
                    provider_subtype = 'firewall_rule',
                    list_fields = (
                        ('name', 'Name'),
                        ('firewall__name', 'Firewall'),
                        ('firewall__network__name', 'Network'),
                        ('mode', 'Mode'),
                        ('from_port', 'From port'),
                        ('to_port', 'To port'),
                        ('protocol', 'Protocol'),
                        ('cidrs', 'CIDRs')
                    ), 
                    scopes = {
                        'network': '--network',
                        'firewall': '--firewall'
                    }
                )
            ))
        )
