from django.db import models as django

from .base import ModelFacade
from .fields import EncryptedDataField

import yaml


class ConfigModelFacadeMixin(ModelFacade):
 
    def get_field_config_display(self, value, short):
        return yaml.dump(value, default_flow_style=False)


class ConfigMixin(django.Model):

    config = EncryptedDataField(default={})

    class Meta:
        abstract = True
