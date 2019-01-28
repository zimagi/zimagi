from systems.command import types, mixins


class ListCommand(
    mixins.op.ListMixin,
    types.ConfigActionCommand
):
    def groups_allowed(self):
        return False # Configuration model access

    def get_description(self, overview):
        if overview:
            return """list configurations in current environment

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """list configurations in current environment
                      
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
        self.parse_config_reference(True)

    def exec(self):
        def process(op, info, key_index):
            if op == 'label':
                info.extend(['Groups'])
            else:
                config = self.get_instance(self._config, info[key_index])
                info.append("\n".join(config.groups.values_list('name', flat = True)))

        self.exec_processed_list(self._config, process,
            ('name', 'Name'),
            ('value', 'Value'),
            ('description', 'Description'),
            ('user', 'User'),
            name__in = [ config.name for config in self.configs ]
        )
