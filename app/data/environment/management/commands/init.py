
from systems import command
from systems.command import mixins


class Command(
    mixins.op.AddMixin,
    command.SimpleCommand
):
    def server_enabled(self):
        return False
    
    def get_priority(self):
        return 9

    def get_command_name(self):
        return 'init'

    def get_description(self, overview):
        if overview:
            return """add and initialize a new cluster environment

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """add and initialize a new cluster environment
                      
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
        self.parse_env()
        self.parse_env_fields()

    def exec(self):
        self.exec_add(self._env, self.env_name, self.env_fields)
