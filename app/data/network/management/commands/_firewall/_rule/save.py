from systems.command import types, mixins


class SaveCommand(
    types.NetworkFirewallActionCommand
):
    def get_description(self, overview):
        if overview:
            return """save a firewall rule in an environment firewall

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """save a firewall rule in an environment firewall
                      
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
        self.parse_test()
        self.parse_force()
        self.parse_network_name('--network')
        self.parse_firewall_name()
        self.parse_firewall_rule_name()
        self.parse_firewall_rule_fields(True, self.get_provider('network', 'help').field_help)

    def exec(self):
        self.set_firewall_scope()
        self.set_firewall_rule_scope()

        if self.check_exists(self._firewall_rule, self.firewall_rule_name):
            self.firewall_rule.provider.update(self.firewall_rule_fields)
        else:
            self.network_provider.firewall_rule.create(
                self.firewall_rule_name, 
                self.firewall, 
                self.firewall_rule_fields
            )
