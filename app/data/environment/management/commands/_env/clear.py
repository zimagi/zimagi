
from django.core.management.base import CommandError

from systems.command import SimpleCommand
from data.environment import models

import re


class ClearCommand(SimpleCommand):

    def get_description(self, overview):
        if overview:
            return """clear all existing cluster environments

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """clear all existing cluster environments
                      
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
        proceed = False

        if len(models.Environment.get_keys()):
            proceed = self.confirmation(self.notice("Are you sure you want to clear ALL environments?", False))
        else:
            self.warning("No environments exist")

        if proceed:
            self.info("Clearing all environments")
            models.State.delete_environment()
        
            if models.Environment.clear():
                self.success(" > Successfully cleared environments")
            else:
                self.error("Environment deletion failed")
        else:
            self.warning("User aborted")
