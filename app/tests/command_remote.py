from django.conf import settings

from tests.command.base import BaseCommandTest


class Test(BaseCommandTest):

    def exec(self):
        self.command._host.store(settings.DEFAULT_HOST_NAME, {
            'host': 'localhost',
            'encryption_key': settings.ADMIN_API_KEY
        })
        super().exec()
        self.command._host.delete(settings.DEFAULT_HOST_NAME)
