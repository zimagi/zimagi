from systems.command import types, mixins


class AddCommand(
    mixins.op.AddMixin,
    types.StorageMountActionCommand
):
    def get_description(self, overview):
        if overview:
            return """add a new storage mount in current environment

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """add a new storage mount in current environment
                      
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
        self.parse_firewall_names('--firewalls')
        self.parse_subnet_name()
        self.parse_storage_name()        
        self.parse_mount_name()
        self.parse_mount_fields(True, self.get_provider('storage', 'help').field_help)

    def exec(self):
        self.set_subnet_scope()
        self.set_storage_scope()
        self.set_mount_scope()
        self.set_firewall_scope()

        if self.check_available(self._mount, self.mount_name):
            mount = self.storage.provider.create_mount(
                self.subnet,
                self.mount_fields,
                firewalls = self.firewalls if self.firewall_names else [],
            )
            instance = self.exec_add(self._mount, self.mount_name, {
                'config': mount.config,
                'remote_host': mount.remote_host,
                'remote_path': mount.remote_path,
                'mount_options': mount.mount_options,
                'subnet': self.subnet
            })
            if mount.firewalls:
                self.exec_add_related(
                    self._firewall,
                    instance, 'firewalls', 
                    mount.firewalls
                )
