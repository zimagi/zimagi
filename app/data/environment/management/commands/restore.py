from django.conf import settings

from systems.command import types, mixins
from systems.db import manager as db


class Command(
    types.EnvironmentActionCommand
):
    def get_command_name(self):
        return 'restore'

    def get_description(self, overview):
        if overview:
            return """restore a cenv evironment from local database

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """restore a cenv evironment from local database
                      
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
    def server_enabled(self):
        return True
    
    def parse(self):
        self.parse_variable('host', False, str, "CEnv host IP address")
        self.parse_variable('token', False, str, "CEnv access token")

    def preprocess(self, params):
        params.data['db'] = db.DatabaseManager().save(encrypted = True)

    def exec(self):
        db.DatabaseManager().load(self.options.get('db'), encrypted = True)
        self.success('Database successfully transferred')
        