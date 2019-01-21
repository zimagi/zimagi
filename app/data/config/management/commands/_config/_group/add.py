from systems.command import types, mixins


class AddCommand(
    mixins.op.AddMixin,
    types.ConfigGroupActionCommand
):
    def get_description(self, overview):
        if overview:
            return """add environment groups to configurations

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """add environment groups to configurations
                      
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
        self.parse_config_reference()
        self.parse_config_groups(None)

    def exec(self):
        def add_groups(config, state):
            self.exec_add_related(
                self._config_group, 
                config, 'groups', 
                self.config_group_names
            )
        self.run_list(self.configs, add_groups)
