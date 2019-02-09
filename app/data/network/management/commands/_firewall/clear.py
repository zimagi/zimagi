from systems.command import types, mixins


class ClearCommand(
    types.NetworkFirewallActionCommand
):
    def get_description(self, overview):
        if overview:
            return """clear all existing firewalls in an environment network

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """clear all existing firewalls in an environment network
                      
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
        self.parse_force()
        self.parse_network_name(True)
    
    def confirm(self):
        self.confirmation()       

    def exec(self):
        self.set_firewall_scope()

        def remove_firewall(firewall, state):
            self.exec_local('firewall rm', {
                'force': self.force,
                'network_name': firewall.network.name,
                'firewall_name': firewall.name
            })
        self.run_list(self.firewalls, remove_firewall)
