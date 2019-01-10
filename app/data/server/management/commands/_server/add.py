from systems.command import types, mixins


class AddCommand(
    mixins.op.AddMixin,
    mixins.data.ServerMixin, 
    types.ServerActionCommand
):
    def get_description(self, overview):
        if overview:
            return """add new servers in current environment

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """add new servers in current environment
                      
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
        self.parse_compute_provider_name()
        self.parse_server_groups(True)
        self.parse_server_fields(True, self.get_compute_provider('help').field_help)

    def exec(self):
        def complete_callback(index, server):
            self.success(server)

            instance = self.exec_add(self._server, server.name, {
                'config': server.config,
                'type': server.type,
                'region': server.region,
                'zone': server.zone,
                'ip': server.ip,
                'user': server.user,
                'password': server.password,
                'private_key': server.private_key,
                'data_device': server.data_device
            })
            self.exec_add_related(
                self._server_group, 
                instance, 'groups', 
                server.groups
            )

        self.compute_provider.create_servers(
            self.server_fields, 
            self.server_group_names, 
            complete_callback
        )        
