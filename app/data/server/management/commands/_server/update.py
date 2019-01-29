from systems.command import types, mixins

import re


class UpdateCommand(
    mixins.op.AddMixin,
    mixins.op.UpdateMixin,
    mixins.op.RemoveMixin,
    types.ServerActionCommand
):
    def get_description(self, overview):
        if overview:
            return """update existing servers in current environment

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """update existing servers in current environment
                      
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
        self.parse_server_groups('--groups')
        self.parse_server_reference()
        self.parse_server_fields(True)

    def exec(self):
        self.set_firewall_scope()
        self.set_server_scope()

        def update_server(server, state):
            if self.server_fields:
                self.exec_update(
                    self._server, 
                    server.name, 
                    self.server_fields
                )
            if self.server_group_names:
                add_groups, remove_groups = self._parse_add_remove_names(self.server_group_names)
                
                if add_groups:
                    self.exec_add_related(
                        self._server_group, 
                        server, 'groups', 
                        add_groups
                    )
                if remove_groups:
                    self.exec_rm_related(
                        self._server_group, 
                        server, 'groups', 
                        remove_groups
                    )
            
            if self.firewall_names:
                add_firewalls, remove_firewalls = self._parse_add_remove_names(self.firewall_names)
                new_firewalls = []

                for firewall in server.firewalls.all():
                    if firewall.name not in remove_firewalls + add_firewalls:
                        new_firewalls.append(firewall)
                
                if add_firewalls:
                    add_firewalls = self.get_instances(self._firewall, names = add_firewalls)
                if remove_firewalls:
                    remove_firewalls = self.get_instances(self._firewall, names = remove_firewalls)
                
                new_firewalls.extend(add_firewalls)
                server.provider.update_firewalls(new_firewalls)

                if add_firewalls:
                    self.exec_add_related(
                        self._firewall, 
                        server, 'firewalls', 
                        add_firewalls
                    )

                if remove_firewalls:
                    self.exec_rm_related(
                        self._firewall, 
                        server, 'firewalls', 
                        remove_firewalls
                    )
         
        self.run_list(self.servers, update_server)
