
from systems.command import SimpleCommand
from data.environment import models
from utility.display import print_table


class GetCommand(SimpleCommand):

    def get_description(self, overview):
        if overview:
            return """get current cluster environment (for all operations)

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """get current cluster environment (for all operations)
                      
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

    def add_arguments(self, parser):
        pass


    def handle(self, *args, **options):
        state = models.State.get_environment()
        
        if state:
            print_table([
                ["Current environment", self.success(state.value, False)],
                ["Last updated", state.timestamp.strftime("%Y-%m-%d %H:%M:%S %Z")]
            ])
        else:
            self.warning("Environment state is not set")
