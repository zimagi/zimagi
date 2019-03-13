from django.conf import settings

from systems.command.providers import data


class BaseGroupProvider(data.DataCommandProvider):

    def __init__(self, name, command, instance = None):
        super().__init__(name, command, instance)
        self.provider_type = 'group'
        self.provider_options = settings.GROUP_PROVIDERS

    @property
    def facade(self):
        return self.command._group
