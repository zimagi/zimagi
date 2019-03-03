from django.db import models as django

from .config import ConfigMixin, ConfigModelFacadeMixin
from .fields import EncryptedDataField

import yaml


class ProviderModelFacadeMixin(ConfigModelFacadeMixin):

    def get_provider_name(self):
        # Override in subclass
        return None
    
    def get_provider_relation(self):
        # Override in subclass
        return None
 
    def get_field_type_display(self, instance, value, short):
        return value
 
    def get_field_variables_display(self, instance, value, short):
        return yaml.dump(value, default_flow_style=False)
 
    def get_field_state_config_display(self, instance, value, short):
        return yaml.dump(value, default_flow_style=False)


class ProviderMixin(ConfigMixin):

    type = django.CharField(null=True, max_length=128)
    variables = EncryptedDataField(default={})
    state_config = EncryptedDataField(default={})

    class Meta:
        abstract = True

    def get_provider_name(self):
        return self.facade.get_provider_name()

    def initialize(self, command):
        super().initialize(command)

        provider_name = self.get_provider_name()
        if provider_name:
            self.provider = command.get_provider(provider_name, self.type, instance = self)
        return True
