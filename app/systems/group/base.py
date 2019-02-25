from django.conf import settings

from systems.command import providers


class BaseGroupProvider(providers.DataCommandProvider):

    def __init__(self, name, command, instance = None):
        super().__init__(name, command, instance)
        self.provider_type = 'group'
        self.provider_options = settings.GROUP_PROVIDERS

    @property
    def facade(self):
        return self.command._group

    def prepare_instance(self, instance, relations, created):
        if 'parent' in relations:
            if relations['parent']:
                instance.parent = self.command.get_instance(self.facade, relations['parent'])
            else:
                instance.parent = None
