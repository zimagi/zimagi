from systems.command import types
from data.network.management.commands import _network as network


class Command(types.NetworkRouterCommand):

    def get_command_name(self):
        return 'network'

    def get_description(self, overview):
        if overview:
            return """manage environment networks

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """manage environment networks
                      
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
            ('list', network.ListCommand),
            ('get', network.GetCommand),
            ('save', network.SaveCommand),
            ('peers', network.PeerCommand),
            ('rm', network.RemoveCommand)
        )
