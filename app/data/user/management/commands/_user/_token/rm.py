
from rest_framework.authtoken.models import Token

from systems.command import types, mixins


class RemoveCommand(
    types.UserTokenActionCommand
):
    def parse(self):
        self.parse_user_name()

    def confirm(self):
        self.confirmation()       

    def exec(self):
        Token.objects.filter(user = self.user).delete()
