from settings import Roles
from systems.command import types, mixins


class ListCommand(
    mixins.op.ListMixin,
    types.NetworkActionCommand
):
    def get_description(self, overview):
        if overview:
            return """list networks in current environment

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """list networks in current environment
                      
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
    def exec(self):
        def process(op, info, key_index):
            if op == 'label':
                info.extend(['Subnets', 'Firewalls'])
            else:
                network = self.get_instance(self._network, info[key_index])
                subnets = []
                firewalls = []
                
                for subnet in network.subnets.all():
                    subnets.append("{} ({})".format(subnet.name, subnet.cidr))
                
                for firewall in network.firewalls.all():
                    firewalls.append("{}".format(firewall.name))
                
                info.append("\n".join(subnets))
                info.append("\n".join(firewalls))

        self.exec_processed_list(self._network, process,
            ('name', 'Name'),
            ('type', 'Type'),
            ('cidr', 'CIDR')
        )
