from systems.command import types, mixins


class ListCommand(
    mixins.op.ListMixin,
    mixins.data.ServerMixin, 
    types.ServerGroupActionCommand
):
    def get_description(self, overview):
        if overview:
            return """list environment groups for server

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """list environment groups for server
                      
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
        self.parse_server_name(True)

    def exec(self):
        if self.server_name:
            self.server # Validate server
            self.exec_list_related(
                self._server, 
                self.server_name, 
                'groups', 
                self._server_group,
                'name'
            )
        else:
            def process(op, info, key_index):
                if op == 'label':
                    info.append('servers')
                else:
                    info.append(", ".join(self._server.field_values('name', groups__name = info[key_index])))

            self.exec_processed_list(self._server_group, process, 'name')
