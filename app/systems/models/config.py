from django.db import models as django

from .base import ModelFacade
from .fields import EncryptedDataField

import yaml


class ConfigModelFacadeMixin(ModelFacade):

    def get_field_config_display(self, instance, value, short):
        if not value:
            return ''
        else:
            return yaml.dump(value, default_flow_style=False).strip()


class ConfigMixin(django.Model):

    config = EncryptedDataField(default={})

    class Meta:
        abstract = True
