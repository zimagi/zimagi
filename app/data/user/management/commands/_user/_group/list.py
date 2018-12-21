from systems.command import types, mixins


class ListCommand(
    mixins.op.ListMixin,
    mixins.data.UserMixin, 
    types.UserGroupActionCommand
):
    def get_description(self, overview):
        if overview:
            return """list environment groups for user

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """list environment groups for user
                      
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
    def parse(self):
        self.parse_user_name(True)

    def exec(self):
        if self.user_name:
            self.user # Validate user
            self.exec_list_related(self._user, self.user_name, 'groups')
        else:
            self.exec_list(self._user_group)
