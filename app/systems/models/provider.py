from django.db import models as django

from .config import ConfigMixin, ConfigModelFacadeMixin
from .fields import EncryptedDataField

import yaml


class ProviderModelFacadeMixin(ConfigModelFacadeMixin):

    @property
    def provider_name(self):
        if getattr(self.meta, 'provider_name', None):
            return self.meta.provider_name
        return None

    @property
    def provider_relation(self):
        if getattr(self.meta, 'provider_relation', None):
            return self.meta.provider_relation
        return None


    def get_field_type_display(self, instance, value, short):
        return value

    def get_field_variables_display(self, instance, value, short):
        if not value:
            return ''
        else:
            return self.encrypted_color(yaml.dump(value))

    def get_field_state_config_display(self, instance, value, short):
        if not value:
            return ''
        else:
            return self.encrypted_color(yaml.dump(value).strip())


class ProviderMixin(ConfigMixin):

    provider_type = django.CharField(null = True, max_length = 128, editable = False)
    variables = EncryptedDataField(default = {}, editable = False)
    state_config = EncryptedDataField(default = {}, editable = False)

    class Meta:
        abstract = True

    def initialize(self, command):
        if not super().initialize(command):
            return False

        provider_name = self.facade.provider_name
        if provider_name:
            self.provider = command.get_provider(provider_name, self.provider_type, instance = self)
        return True
