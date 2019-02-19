from django.conf import settings

from systems.command import types, mixins


class Command(
    mixins.data.NetworkMixin,
    types.EnvironmentActionCommand
):
    def get_command_name(self):
        return 'provision'

    def get_description(self, overview):
        if overview:
            return """provision a cluster profile

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """provision a cluster profile
                      
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
        self.parse_profile_components('--components')
        self.parse_project_name()
        self.parse_profile_name()
        self.parse_profile_fields(True)

    def exec(self):
        self.project.provider.provision_profile(
            self.profile_name,
            self.profile_component_names, 
            self.profile_fields
        )
