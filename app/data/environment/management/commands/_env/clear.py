
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
        state = models.State.objects.get(name = 'environment')
        queryset = models.Environment.objects.all()
        proceed = False

        if len(queryset.values_list('name', flat=True)):
            confirmation = input(self.style.NOTICE("Are you sure you want to clear ALL environments? (type YES to confirm): "))    

            if re.match(r'^[Yy][Ee][Ss]$', confirmation):
                proceed = True
        else:
            raise CommandError(self.style.WARNING("No environments exist"))

        if proceed:
            print("Clearing all environments")
            qs_deleted, qs_del_per_type = queryset.delete()
            st_deleted, st_del_per_type = state.delete()
        
            if qs_deleted:
                print(self.style.SUCCESS(" > Successfully cleared environments"))
            else:
                raise CommandError(self.style.ERROR("Environment deletion failed"))
        else:
            raise CommandError(self.style.WARNING("User aborted"))
