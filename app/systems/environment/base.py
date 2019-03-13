from django.conf import settings

from systems.command.providers import data


class BaseEnvironmentProvider(data.DataCommandProvider):

    def __init__(self, name, command, instance = None):
        super().__init__(name, command, instance)
        self.provider_type = 'env'
        self.provider_options = settings.ENVIRONMENT_PROVIDERS

    @property
    def facade(self):
        return self.command._env
