from systems.command import types, mixins


class SetCommand(
    mixins.op.UpdateMixin,
    types.ConfigActionCommand
):
    def get_description(self, overview):
        if overview:
            return """set environment configuration value

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """set environment configuration value
                      
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
        self.parse_config_name()
        self.parse_config_value()
        self.parse_config_description(True)

    def exec(self):
        self.exec_update(self._config, self.config_name, {
            'value': self.config_value,
            'user': self.active_user.username if self.active_user else None,
            'description': self.config_description
        })
