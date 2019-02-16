from systems.command import types, mixins


class PeerCommand(
    types.NetworkActionCommand
):
    def get_description(self, overview):
        if overview:
            return """update existing environment network peers

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """update existing environment network peers
                      
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
        self.parse_clear()
        self.parse_network_provider_name()
        self.parse_network_peer_name()
        self.parse_network_names(False)

    def exec(self):
        if self.clear:
            self.network_peer.provider.delete()
        else:
            if self.check_available(self._network_peer, self.network_peer_name):
                self.network_provider.network_peer.create(self.network_peer_name, self.network_names)
            else:
                self.network_peer.provider.update(self.network_names)
