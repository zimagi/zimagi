
from systems import command
from systems.command import mixins


class ListCommand(
    mixins.data.UserMixin,
    command.SimpleCommand
):
    def groups_allowed(self):
        return ['admin']

    def get_description(self, overview):
        if overview:
            return """list users in current environment

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """list users in current environment
                      
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
    def exec(self):
        data = self._user.render(self._user.values(
            'id', 
            'username',
            'first_name',
            'last_name',
            'email'
        ))
        name_index = data[0].index('username')

        for index, user in enumerate(data):
            if index == 0:
                user.append('groups')
            else:
                user.append(", ".join(self._user.retrieve(user[name_index]).groups.values_list('name', flat = True)))

        self.print_table(data)
