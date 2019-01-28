from systems.command import types, mixins


class RemoveCommand(
    mixins.op.RemoveMixin,
    types.NetworkSubnetActionCommand
):
    def get_description(self, overview):
        if overview:
            return """remove an existing subnet in an environment network

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """remove an existing subnet in an environment network
                      
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
        self.parse_network_name('--network')
        self.parse_subnet_name()

    def confirm(self):
        self.confirmation()       

    def exec(self):
        self.set_subnet_scope()
        if self.subnet:
            self.network.provider.destroy_subnet(self.subnet)
            self.exec_rm(self._subnet, self.subnet_name)
