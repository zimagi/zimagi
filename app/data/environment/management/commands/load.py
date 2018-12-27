from systems.command import types, mixins
from systems.db import manager


class Command(
    types.EnvironmentActionCommand
):
    def server_enabled(self):
        return True

    def get_command_name(self):
        return 'load'

    def get_description(self, overview):
        if overview:
            return """load data into database from data file

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """load data into database from data file
                      
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
    def exec(self):
        try:
            manager.DatabaseManager().load_file(encrypted = True)
        except Exception as e:
            self.error(e)
        
        self.success("Successfully loaded database package")
