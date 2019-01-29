from systems.command import types, mixins


class GroupCommand(
    mixins.op.UpdateMixin,
    types.ServerActionCommand
):
    def get_description(self, overview):
        if overview:
            return """add environment group children

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """add environment group children
                      
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
        self.parse_server_group(help_text = 'parent server group name')
        self.parse_server_groups(False, help_text = 'one or more child server group names')

    def exec(self):
        parent = self.exec_update(self._server_group, self.server_group_name)

        for group in self.server_group_names:
            self.exec_update(self._server_group, group, { 
                'parent': parent
            })
