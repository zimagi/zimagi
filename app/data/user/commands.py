from django.conf import settings

from settings.roles import Roles
from base.command.base import command_set
from base.command.router import RouterCommand
from base.command.action import ActionCommand
from systems.command.factory import resource


class UserRouterCommand(RouterCommand):

    def get_priority(self):
        return 85


class UserActionCommand(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.user_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 85


class RotateCommand(
    UserActionCommand
):
    def parse(self):
        self.parse_user_name(True)

    def exec(self):
        if not settings.API_EXEC:
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


class Command(UserRouterCommand):

    def get_subcommands(self):
        return command_set(
            resource.ResourceCommandSet(
                UserActionCommand, self.name,
                provider_name = self.name
            ),
            ('rotate', RotateCommand)
        )
