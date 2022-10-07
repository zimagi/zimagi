from django.conf import settings

from systems.commands.action import ActionCommand
from tests.command.base import BaseCommandTest


class Test(BaseCommandTest):

    def exec(self):
        command = ActionCommand('command_test_case')

        command._host.store(settings.DEFAULT_HOST_NAME, {
            'host': 'localhost',
            'encryption_key': settings.ADMIN_API_KEY
        })
        super().exec()
        command._host.delete(settings.DEFAULT_HOST_NAME)
