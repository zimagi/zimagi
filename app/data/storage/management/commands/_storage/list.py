from settings import Roles
from systems.command import types, mixins


class ListCommand(
    mixins.op.ListMixin,
    types.StorageActionCommand
):
    def get_description(self, overview):
        if overview:
            return """list storage sources in current environment

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """list storage sources in current environment
                      
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
        self.parse_network_name(True)

    def exec(self):
        self.set_storage_scope()

        def process(op, info, key_index):
            if op == 'label':
                info.extend(['Mount', 'Host', 'Path'])
            else:
                storage = self.get_instance(self._storage, info[key_index])
                mount_names = []
                mount_hosts = []
                mount_paths = []
                
                for mount in storage.mounts.all():
                    mounts.append(mount.name)
                    mounts.append(mount.remote_host)
                    mounts.append(mount.remote_path)
                
                info.append("\n".join(mount_names))
                info.append("\n".join(mount_hosts))
                info.append("\n".join(mount_paths))

        self.exec_processed_list(self._storage, process,
            ('name', 'Name'),
            ('type', 'Type')
        )
