from systems.command.base import command_list
from systems.command import types, mixins, factory


class TokenActionResult(types.ActionResult):

    @property
    def user_name(self):
        return self.get_named_data('name')

    @property
    def user_token(self):
        return self.get_named_data('token')


class RotateCommand(
    types.UserActionCommand
):
    def get_action_result(self, messages = []):
        return TokenActionResult(messages)

    def parse(self):
        self.parse_user_name(True)

    def exec(self):
        user = self.user if self.user_name else self.active_user
        token = self._user.generate_token()

        try:
            user.set_password(token)
            user.save()
        
        except Exception as e:
            self.error(e)

        self.silent_data('name', user.name)
        self.data("User {} token:".format(user.name), token, 'token')
        
    def postprocess(self, result):
        curr_env = self.get_env()

        if curr_env.user == result.user_name:
            try:
                curr_env.token = result.user_token
                curr_env.save()
            
            except Exception as e:
                self.error(e)


class Command(types.UserRouterCommand):

    def get_command_name(self):
        return 'user'

    def get_subcommands(self):
        return command_list(
            factory.ResourceCommands(
                types.UserActionCommand, 'user',
                relations = {
                    'groups': ('group_names', '--groups')
                }
            ),
            ('rotate', RotateCommand)
        )
