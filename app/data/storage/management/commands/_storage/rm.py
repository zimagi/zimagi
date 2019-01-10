from systems.command import types, mixins


class RemoveCommand(
    mixins.op.RemoveMixin,
    mixins.data.StorageMixin, 
    types.StorageActionCommand
):
    def get_description(self, overview):
        if overview:
            return """remove an existing storage mount in current environment

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """remove an existing storage mount in current environment
                      
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
        self.parse_storage_reference()

    def confirm(self):
        self.confirmation()       

    def exec(self):
        def remove_storage(storage, state):
            storage.storage_provider.destroy_storage_mount()
            self.exec_rm(self._storage, storage.name)

        self.run_list(self.mounts, remove_storage)
