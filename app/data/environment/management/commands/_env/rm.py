
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
        env_name = options['environment'][0]
        queryset = models.Environment.objects.filter(name = env_name)
        proceed = False
        
        if len(queryset.values_list('name', flat=True)):
            confirmation = input("Are you sure you want to remove environment: {} ? (type YES to confirm): ".format(self.style.NOTICE(env_name)))    

            if re.match(r'^[Yy][Ee][Ss]$', confirmation):
                proceed = True
        else:
            raise CommandError(self.style.WARNING("Environment does not exist"))

        if proceed:
            print("Removing environment: {}".format(self.style.NOTICE(env_name)))
            deleted, del_per_type = queryset.delete()
        
            if deleted:
                print(self.style.SUCCESS(" > Successfully deleted environment"))
            else:
                raise CommandError(self.style.ERROR("Environment deletion failed"))
        else:
            raise CommandError(self.style.WARNING("User aborted"))            
