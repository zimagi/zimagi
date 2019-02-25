from django.conf import settings

from systems.command import providers


class BaseUserProvider(providers.DataCommandProvider):

    def __init__(self, name, command, instance = None):
        super().__init__(name, command, instance)
        self.provider_type = 'user'
        self.provider_options = settings.USER_PROVIDERS

    @property
    def facade(self):
        return self.command._user

    def save_related(self, instance, relations, created):
        if 'groups' in relations:
            self.update_related(instance, 'groups',
                self.command._group, 
                relations['groups']
            )
