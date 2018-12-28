from rest_framework.authtoken.models import Token

from systems.command import types, mixins
from utility import common


class TokenActionResult(types.ActionResult):

    @property
    def user_token(self):
        return self.get_named_data('token')


class RotateCommand(
    types.UserTokenActionCommand
):
    def get_action_result(self, messages = []):
        return TokenActionResult(messages)

    def get_description(self, overview):
        if overview:
            return """rotate a user API token for environment

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam 
pulvinar nisl ac magna ultricies dignissim. Praesent eu feugiat 
elit. Cras porta magna vel blandit euismod.
"""
        else:
            return """rotate a user API token for environment
                      
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
        user = self.get_token_user()
        token = common.generate_token()

        try:
            Token.objects.filter(user = user).delete()
            token = Token.objects.create(user = user, key = token)

            user.set_password(token)
            user.save()
        
        except Exception as e:
            self.error(e)

        self.data("User {} token:".format(user.username), token.key, 'token')
        
    def process(self, result):
        if self.curr_env.user == result.active_user:
            try:
                self.curr_env.token = result.user_token
                self.curr_env.save()
            
            except Exception as e:
                self.error(e)
