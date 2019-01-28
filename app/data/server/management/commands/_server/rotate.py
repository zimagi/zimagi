from systems.command import types, mixins


class RotateCommand(
    types.ServerActionCommand
):
    def get_description(self, overview):
        if overview:
            return """rotate credentials of existing servers in current environment

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """rotate credentials of existing servers in current environment
                      
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
        self.parse_server_reference(True)

    def exec(self):
        self.set_server_scope()

        def rotate_server(server, state):
            self.data("Rotating SSH keypair for", str(server))
            
            server.provider.rotate_password()
            server.provider.rotate_key()
            
            self._server.store(server.name,
                ip = server.ip,
                password = server.password,
                private_key = server.private_key
            )
        self.run_list(self.servers, rotate_server)
