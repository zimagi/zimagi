from rest_framework.authtoken.models import Token

from systems.command import types, mixins


class GetCommand(
    types.UserTokenActionCommand
):
    def parse(self):
        self.parse_user_name(True)

    def exec(self):
        user = self.get_token_user()

        try:
            token = Token.objects.get(user = user)
            self.data("User {} token".format(user.username), token.key, 'token')
        except Token.DoesNotExist:
            self.error("User {} token does not exist".format(user.username))
