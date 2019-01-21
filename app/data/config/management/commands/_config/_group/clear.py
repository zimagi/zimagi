from systems.command import types, mixins


class ClearCommand(
    mixins.op.RemoveMixin,
    types.ConfigGroupActionCommand
):
    def get_description(self, overview):
        if overview:
            return """clear all environment groups from configuration

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """clear all environment groups from configuration
                      
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
        self.parse_config_groups(True)

    def confirm(self):
        self.confirmation()       

    def exec(self):
        def remove_groups(config, state):
            self.exec_rm_related(
                self._config_group, 
                config, 'groups', 
                self.config_group_names
            )    
        self.run_list(self.get_instances(self._config), remove_groups)

        for group in self.config_group_names:
            self.exec_rm(self._config_group, group)
