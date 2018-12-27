from systems.command import types, mixins


class ClearCommand(
    mixins.op.ClearMixin,
    types.UserGroupActionCommand
):
    def get_description(self, overview):
        if overview:
            return """clear all environment groups from user

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """clear all environment groups from user
                      
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

    def confirm(self):
        if self._user_group.count():
            self.confirmation()       

    def exec(self):
        if self.user_name:
            self.exec_clear_related(self._user_group, self.user, 'groups')
        else:
            for user in self._user.all():
                self.exec_clear_related(self._user_group, user, 'groups')
            
            self.exec_clear(self._user_group)
