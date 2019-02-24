from django.db import models as django

from .base import ModelFacade
from .fields import EncryptedDataField


class ConfigModelFacadeMixin(ModelFacade):
    pass


class ConfigMixin(django.Model):

    config = EncryptedDataField(default={})

    class Meta:
        abstract = True
