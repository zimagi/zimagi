from systems.command.base import command_list
from systems.command import types, factory


class Command(types.NetworkFirewallRouterCommand):

    def get_command_name(self):
        return 'firewall'

    def get_subcommands(self):
        network_provider_name = 'network'
        firewall_name = self.get_command_name()
        firewall_rule_name = 'firewall_rule'

        return command_list(
            factory.ResourceCommandSet(
                types.NetworkFirewallActionCommand, firewall_name,
                provider_name = network_provider_name,
                provider_subtype = firewall_name
            ),
            ('rule', factory.Router(
                types.NetworkFirewallRouterCommand,
                factory.ResourceCommandSet(
                    types.NetworkFirewallActionCommand, firewall_rule_name,
                    provider_name = network_provider_name,
                    provider_subtype = firewall_rule_name
                )
            ))
        )
