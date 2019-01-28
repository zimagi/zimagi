from settings import Roles
from systems.command import types, mixins


class ListCommand(
    mixins.op.ListMixin,
    types.ServerGroupActionCommand
):
    def groups_allowed(self):
        return False # Server access model

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
        self.parse_server_groups(True)

    def exec(self):
        def process(op, info, key_index):
            if op == 'label':
                info.extend(['server', 'type', 'region', 'zone', 'ip', 'state'])
            else:
                server_names = []
                server_types = []
                server_regions = []
                server_zones = []
                server_ips = []
                server_states = []

                for server in self.get_instances(self._server, groups = info[key_index]):
                    server_names.append(server.name)
                    server_types.append(server.type)
                    server_regions.append(server.region)
                    server_zones.append(server.zone)
                    server_ips.append(server.ip)
                    server_states.append(server.state)
                    
                info.append("\n".join(server_names))
                info.append("\n".join(server_types))
                info.append("\n".join(server_regions))
                info.append("\n".join(server_zones))
                info.append("\n".join(server_ips))
                info.append("\n".join(server_states))

        if self.server_group_names:
            self.exec_processed_sectioned_list(
                self._server_group, process, 
                'name', 'parent',
                name__in = self.server_group_names
            )
        else:
            self.exec_processed_sectioned_list(self._server_group, process, 'name', 'parent')
