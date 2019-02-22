from rest_framework.authtoken.models import Token

from systems.command import types, mixins


class TokenActionResult(types.ActionResult):

    @property
    def user_token(self):
        return self.get_named_data('token')


class RotateCommand(
    types.UserTokenActionCommand
):
    def get_action_result(self, messages = []):
        return TokenActionResult(messages)

    def parse(self):
        self.parse_user_name(True)

    def exec(self):
        user = self.get_token_user()
        token = self._user.generate_token()

        try:
            Token.objects.filter(user = user).delete()
            token = Token.objects.create(user = user, key = token)

            user.set_password(token)
            user.save()
        
        except Exception as e:
            self.error(e)

        self.data("User {} token:".format(user.username), token.key, 'token')
        
    def postprocess(self, result):
        curr_env = self.get_env()

        if curr_env.user == result.active_user:
            try:
                curr_env.token = result.user_token
                curr_env.save()
            
            except Exception as e:
                self.error(e)
