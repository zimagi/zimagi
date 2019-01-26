from systems.command import types, mixins


class AddCommand(
    mixins.op.AddMixin,
    mixins.data.NetworkMixin, 
    types.NetworkFirewallActionCommand
):
    def get_description(self, overview):
        if overview:
            return """add a new firewall rule in an environment firewall

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """add a new firewall rule in an environment firewall
                      
Etiam mattis iaculis felis eu pharetra. Nulla facilisi. 
Duis placerat pulvinar urna et elementum. Mauris enim risus, 
mattis vel risus quis, imperdiet convallis felis. Donec iaculis 
tristique diam eget rutrum.

Etiam sit amet mollis lacus. Nulla pretium, neque id porta feugiat, 
erat sapien sollicitudin tellus, vel fermentum quam purus non sem. 
Mauris venenatis eleifend nulla, ac facilisis nulla efficitur sed. 
Etiam a ipsum odio. Curabitur magna mi, ornare sit amet nulla at, 
scelerisque tristique leo. Curabitur ut faucibus leo, non tincidunt 
velit. Aenean sit amet consequat mauris.
"""
    def parse(self):
        self.parse_network_name()
        self.parse_firewall_name()
        self.parse_firewall_rule_name()
        self.parse_firewall_rule_fields(True, self.get_provider('network', 'help').field_help)

    def exec(self):
        self._firewall_rule.set_scope(self.firewall)

        if self.check_available(self._firewall_rule, self.firewall_name):
            rule = self.network.provider.create_firewall_rule(self.firewall, self.firewall_rule_name, self.firewall_rule_fields)
            self.exec_add(self._firewall_rule, self.firewall_rule_name, {
                'config': rule.config,
                'type': rule.type,
                'from_port': rule.from_port,
                'to_port': rule.to_port,
                'protocol': rule.protocol,
                'cidrs': rule.cidrs
            })
