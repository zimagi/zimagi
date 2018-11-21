
from django.core.management.base import CommandError

from systems.command import SimpleCommand
from data.environment import models

import re


class RemoveCommand(SimpleCommand):

    def get_description(self, overview):
        if overview:
            return """remove an existing cluster environment

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """remove an existing cluster environment
                      
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
        proceed = False
        
        if models.Environment.retrieve(name):
            proceed = self.confirmation("Are you sure you want to remove environment: {} ?".format(self.notice(name, False)))
        else:
            self.warning("Environment does not exist")

        if proceed:
            self.info("Removing environment: {}".format(self.notice(name, False)))
            environment = models.State.get_environment()

            if environment and name == environment.value:
                models.State.delete_environment()    

            if models.Environment.delete(name):
                self.success(" > Successfully deleted environment")
            else:
                self.error("Environment deletion failed")
        else:
            self.warning("User aborted")          
