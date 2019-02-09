from systems.command import types, mixins


class UpdateCommand(
    types.StorageMountActionCommand
):
    def get_description(self, overview):
        if overview:
            return """update existing storage mounts in current environment

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """update existing storage mounts in current environment
                      
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
        self.parse_firewall_names('--firewalls')
        self.parse_mount_name()
        self.parse_mount_fields(True)

    def exec(self):
        self.set_mount_scope()
        self.mount.provider.update(
            self.mount_fields,
            firewalls = self.firewall_names
        )