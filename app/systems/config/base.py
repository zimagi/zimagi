from django.conf import settings

from systems.command.providers import data


class BaseConfigProvider(data.DataCommandProvider):

    def __init__(self, name, command, instance = None):
        super().__init__(name, command, instance)
        self.provider_type = 'config'
        self.provider_options = settings.CONFIG_PROVIDERS

    @property
    def facade(self):
        return self.command._config
