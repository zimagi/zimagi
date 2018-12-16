
from rest_framework.authtoken.models import Token

from systems.command.types import action
from systems.command import mixins


class GetCommand(
    mixins.data.UserMixin, 
    action.ActionCommand
):
    def groups_allowed(self):
        return ['admin']

    def get_description(self, overview):
        if overview:
            return """get user API token for environment

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """get user API token for environment
                      
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
        self.parse_user()

    def exec(self):
        try:
            token = Token.objects.get(user = self.user)
            self.data("User {} token:".format(self.user_name), token, 'token')
        except Token.DoesNotExist:
            self.error("User {} token does not exist".format(self.user_name))
