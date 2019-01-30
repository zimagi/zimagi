from systems.command import types, mixins


class AddCommand(
    mixins.op.AddMixin,
    types.StorageActionCommand
):
    def get_description(self, overview):
        if overview:
            return """add a new storage source in current environment

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """add a new storage source in current environment
                      
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
        self.parse_storage_provider_name()
        self.parse_storage_name()
        self.parse_storage_fields(True, self.get_provider('storage', 'help').field_help)

    def exec(self):
        self.set_storage_scope()

        if self.check_available(self._storage, self.storage_name):
            storage = self.storage_provider.create_storage(
                self.storage_name, 
                self.network, 
                self.storage_fields
            )
            self.exec_add(self._storage, self.storage_name, {
                'config': storage.config,
                'type': storage.type
            })
