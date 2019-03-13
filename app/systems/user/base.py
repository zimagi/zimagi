from django.conf import settings

from systems.command.providers import data


class BaseUserProvider(data.DataCommandProvider):

    def __init__(self, name, command, instance = None):
        super().__init__(name, command, instance)
        self.provider_type = 'user'
        self.provider_options = settings.USER_PROVIDERS

    @property
    def facade(self):
        return self.command._user
