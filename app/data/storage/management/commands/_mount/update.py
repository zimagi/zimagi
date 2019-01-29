from systems.command import types, mixins

import re


class UpdateCommand(
    mixins.op.AddMixin,
    mixins.op.UpdateMixin,
    mixins.op.RemoveMixin,
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
        self.parse_network_name('--network')
        self.parse_firewall_names('--firewalls')
        self.parse_mount_name()
        self.parse_mount_fields(True)

    def exec(self):
        self.set_mount_scope()

        if self.mount_fields:
            self.exec_update(
                self._mount, 
                self.mount_name, 
                self.mount_fields
            )
           
        if self.firewall_names:
            add_firewalls, remove_firewalls = self._parse_add_remove_names(self.firewall_names)
            new_firewalls = []

            for firewall in mount.firewalls.all():
                if firewall.name not in remove_firewalls + add_firewalls:
                    new_firewalls.append(firewall)
                
            if add_firewalls:
                add_firewalls = self.get_instances(self._firewall, names = add_firewalls)
            if remove_firewalls:
                remove_firewalls = self.get_instances(self._firewall, names = remove_firewalls)
                
            new_firewalls.extend(add_firewalls)
            mount.storage.provider.update_mount_firewalls(mount, new_firewalls)

            if add_firewalls:
                self.exec_add_related(
                    self._firewall, 
                    mount, 'firewalls', 
                    add_firewalls
                )

            if remove_firewalls:
                self.exec_rm_related(
                    self._firewall, 
                    mount, 'firewalls', 
                    remove_firewalls
                )
