from settings import Roles
from systems.command import types, mixins


class ListCommand(
    mixins.op.ListMixin,
    mixins.data.NetworkMixin,
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
                info.extend(['firewall', 'type'])
            else:
                firewall_names = []
                firewall_types = []

                for firewall in self._firewall.query(network__name = info[key_index]):
                    firewall_names.append(firewall.name)
                    firewall_types.append(firewall.network.type)
                    
                info.append("\n".join(firewall_names))
                info.append("\n".join(firewall_types))

        if self.network_name:
            self._firewall.set_scope(self.network)
            self.exec_list(self._firewall,
                'name',
                'network__type'
            )
        else:
            self.exec_processed_sectioned_list(self._network, process, 'name')
