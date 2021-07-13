from django.conf import settings

from systems.commands.index import Command


class Rotate(Command('user.rotate')):

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
        host = self.get_host()
        if host.user == result.get_named_data('name'):
            self.save_host(token = result.get_named_data('token'))
