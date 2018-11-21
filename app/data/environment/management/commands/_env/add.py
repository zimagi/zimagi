
from systems.command import SimpleCommand
from data.environment import models


class AddCommand(SimpleCommand):

    def get_description(self, overview):
        if overview:
            return """add a new cluster environment

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """add a new cluster environment
                      
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
        parser.add_argument('environment', nargs=1, type=str, help="environment name")


    def handle(self, *args, **options):
        name = options['environment'][0]
        
        self.info("Creating environment: {}".format(self.success(name, False)))
        environment, created = models.Environment.store(name)
        
        if created:
            self.success(" > Successfully created environment")
        else:
            self.warning("Environment already exists")
