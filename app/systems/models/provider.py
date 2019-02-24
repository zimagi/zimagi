from django.db import models as django

from .config import ConfigMixin, ConfigModelFacadeMixin
from .fields import EncryptedDataField


class ProviderModelFacadeMixin(ConfigModelFacadeMixin):
    pass


class ProviderMixin(ConfigMixin):

    type = django.CharField(null=True, max_length=128)
    variables = EncryptedDataField(default={})
    state_config = EncryptedDataField(default={})

    class Meta:
        abstract = True

    def get_provider_name(self):
        # Override in subclass
        return None

    def initialize(self, command):
        super().initialize(command)

        provider_name = self.get_provider_name()
        if provider_name:
            self.provider = command.get_provider(provider_name, self.type, instance = self)
        return True
