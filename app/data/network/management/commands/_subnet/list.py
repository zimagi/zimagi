from systems.command import types, mixins


class ListCommand(
    mixins.op.ListMixin,
    types.NetworkSubnetActionCommand
):
    def get_description(self, overview):
        if overview:
            return """list subnets in an environment network

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """list subnets in an environment network
                      
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
                info.extend(['subnet', 'type', 'cidr'])
            else:
                subnet_names = []
                subnet_types = []
                subnet_cidrs = []

                for subnet in self._subnet.query(network__name = info[key_index]):
                    subnet_names.append(subnet.name)
                    subnet_types.append(subnet.network.type)
                    subnet_cidrs.append(subnet.cidr)
                    
                info.append("\n".join(subnet_names))
                info.append("\n".join(subnet_types))
                info.append("\n".join(subnet_cidrs))

        if self.network_name:
            self.set_subnet_scope()
            self.exec_list(self._subnet,
                'name',
                'network__name',
                'network__type',
                'cidr'
            )
        else:
            self.exec_processed_sectioned_list(self._network, process, 'name')
