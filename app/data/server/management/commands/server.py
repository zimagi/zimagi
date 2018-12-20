
from systems.command.types import router
from data.server.management.commands import _server as server


class Command(router.RouterCommand):

    def get_priority(self):
        return 2

    def get_command_name(self):
        return 'server'

    def get_description(self, overview):
        if overview:
            return """manage environment servers

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """manage environment servers
                      
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
    def get_subcommands(self):
        return (
            ('list', server.ListCommand),
            ('add', server.AddCommand),
            ('update', server.UpdateCommand),
            ('rm', server.RemoveCommand),
            ('clear', server.ClearCommand)
        )
