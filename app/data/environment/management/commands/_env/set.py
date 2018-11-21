from django.core.management.base import CommandError

from systems.command import SimpleCommand
from data.environment import models


class SetCommand(SimpleCommand):

    def get_description(self, overview):
        if overview:
            return """set current cluster environment (for all operations)

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """set current cluster environment (for all operations)
                      
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
        
        self.info("Setting current environment: {}".format(self.success(name, False)))

        if not models.Environment.retrieve(name):
            self.error("Environment does not exist")

        state, created = models.State.set_environment(name)

        if created:
            self.success(" > Successfully created environment state")
        else:
            self.success(" > Successfully updated environment state")
