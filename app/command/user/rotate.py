from django.conf import settings

from settings.roles import Roles
from systems.command.action import ActionCommand


class Command(ActionCommand):

    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.user_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 85

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
