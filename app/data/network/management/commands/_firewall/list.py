from systems.command import types, mixins


class ListCommand(
    mixins.op.ListMixin,
    types.NetworkFirewallActionCommand
):
    def get_description(self, overview):
        if overview:
            return """list firewalls in an environment network

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """list firewalls in an environment network
                      
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
        self.parse_network_name(True)

    def exec(self):
        def process(op, info, key_index):
            if op == 'label':
                info.extend(['Firewall', 'Type', 'Description'])
            else:
                firewall_names = []
                firewall_types = []
                firewall_descriptions = []

                for firewall in self._firewall.query(network__name = info[key_index]):
                    firewall_names.append(firewall.name)
                    firewall_types.append(firewall.network.type)
                    firewall_descriptions.append(firewall.description)
                    
                info.append("\n".join(firewall_names))
                info.append("\n".join(firewall_types))
                info.append("\n".join(firewall_descriptions))

        if self.network_name:
            self.set_firewall_scope()
            self.exec_list(self._firewall,
                ('name', 'Name'),
                ('network__name', 'Network'),
                ('network__type', 'Network type'),
                ('description', 'Description')
            )
        else:
            self.exec_processed_sectioned_list(self._network, process, ('name', 'Network'))
