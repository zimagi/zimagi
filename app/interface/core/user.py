from systems.command.base import command_list
from systems.command.factory import resource
from systems.command.types import user


class RotateCommand(
    user.UserActionCommand
):
    def parse(self):
        self.parse_user_name(True)

    def exec(self):
        env = self.get_env()
        if not env.host or not env.user:
            self.error("The user rotate command can only be run with a remote environment specified")

        user = self.user if self.user_name else self.active_user
        token = self._user.generate_token()

        user.set_password(token)
        user.save()

        self.silent_data('name', user.name)
        self.data("User {} token:".format(user.name), token, 'token')

    def postprocess(self, result):
        env = self.get_env()
        if env.user == result.get_named_data('name'):
            self.update_env_host(token = result.get_named_data('token'))


class Command(user.UserRouterCommand):

    def get_subcommands(self):
        return command_list(
            resource.ResourceCommandSet(
                user.UserActionCommand, self.name,
                provider_name = self.name
            ),
            ('rotate', RotateCommand)
        )
