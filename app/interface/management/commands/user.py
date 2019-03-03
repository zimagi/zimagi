from systems.command.base import command_list
from systems.command import types, mixins, factory


class RotateCommand(
    types.UserActionCommand
):
    def parse(self):
        self.parse_user_name(True)

    def exec(self):
        user = self.user if self.user_name else self.active_user
        token = self._user.generate_token()
        
        user.set_password(token)
        user.save()

        self.silent_data('name', user.name)
        self.data("User {} token:".format(user.name), token, 'token')
        
    def postprocess(self, result):
        curr_env = self.get_env()
        if curr_env.user == result.get_named_data('name'):
            curr_env.token = result.get_named_data('token')
            curr_env.save()


class Command(types.UserRouterCommand):

    def get_command_name(self):
        return 'user'

    def get_subcommands(self):
        base_name = self.get_command_name()
        return command_list(
            factory.ResourceCommandSet(
                types.UserActionCommand, base_name,
                provider_name = base_name
            ),
            ('rotate', RotateCommand)
        )
