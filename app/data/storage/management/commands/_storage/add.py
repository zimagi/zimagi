from systems.command import types, mixins


class AddCommand(
    mixins.op.AddMixin,
    mixins.data.StorageMixin, 
    types.StorageActionCommand
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
        self.parse_storage_provider_name()
        self.parse_storage_fields(True, self.get_provider('storage', 'help').field_help)

    def exec(self):
        def complete_callback(index, storage):
            self.exec_add(self._storage, storage.name, {
                'config': storage.config,
                'type': storage.type,
                'fs_name': storage.fs_name,
                'region': storage.region,
                'zone': storage.zone,
                'remote_host': storage.remote_host,
                'remote_path': storage.remote_path,
                'mount_options': storage.mount_options
            })
            self.success(storage)
        
        self.storage_provider.create_storage_mounts(
            self.storage_fields,
            complete_callback
        )
