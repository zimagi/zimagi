from settings import Roles
from systems.command import types, mixins


class ListCommand(
    mixins.op.ListMixin,
    types.StorageMountActionCommand
):
    def get_description(self, overview):
        if overview:
            return """list storage mounts in current environment

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """list storage mounts in current environment
                      
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
        self.parse_storage_name(True)

    def exec(self):
        def process(op, info, key_index):
            if op == 'label':
                info.extend(['Mount', 'Remote host', 'Remote path'])
            else:
                mount_names = []
                mount_hosts = []
                mount_paths = []

                for mount in self._mount.query(storage__name = info[key_index]):
                    mount_names.append(mount.name)
                    mount_hosts.append(mount.remote_host)
                    mount_paths.append(mount.remote_path)
                    
                info.append("\n".join(mount_names))
                info.append("\n".join(mount_hosts))
                info.append("\n".join(mount_paths))

        if self.storage_name:
            self.set_mount_scope()
            self.exec_list(self._mount,
                ('name', 'Name'),
                ('storage__name', 'Storage'),
                ('storage__type', 'Storage type'),
                ('remote_host', 'Remote host'),
                ('remote_path', 'Remote path')
            )
        else:
            self.exec_processed_sectioned_list(self._storage, process, 
                ('name', 'Storage source'),
                ('type', 'Type')
            )
