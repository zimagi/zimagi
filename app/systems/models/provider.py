from systems import models

from .config import ConfigMixin, ConfigModelFacadeMixin


class ProviderModelFacadeMixin(ConfigModelFacadeMixin):
    pass


class ProviderMixin(ConfigMixin):

    type = models.CharField(null=True, max_length=128)
    variables = models.EncryptedTextField(default={})
    state_config = models.EncryptedTextField(default={})

    def get_provider_name(self):
        # Override in subclass
        return None

    def initialize(self, command):
        super().initialize(command)

        provider_name = self.get_provider_name()
        if provider_name:
            self.provider = command.get_provider(provider_name, self.type, instance = self)
        return True
