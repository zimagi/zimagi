from django.conf import settings
from django.db import models as django
from django.db.models.base import ModelBase
from django.db.models.manager import Manager
from django.utils.timezone import now

from .facade import ModelFacade

import sys
import inspect
import copy
import re


django.options.DEFAULT_NAMES += (
    'facade_class',
    'scope',
    'scope_process',
    'relation',
    'dynamic_fields',
    'search_fields',
    'ordering_fields',
    'provider_name',
    'provider_relation',
    'command_base'
)


def format_choices(*choices):
    return [ (choice, choice) for choice in choices ]


class DatabaseAccessError(Exception):
    pass


class FacadeMetaModel(ModelBase):

    def __init__(cls, name, bases, attr):
        if not cls._meta.abstract:
            facade_class = cls._meta.facade_class

            if facade_class and inspect.isclass(facade_class):
                cls.facade = facade_class(cls)


class CustomMetaModel(FacadeMetaModel):

    def __new__(cls, name, bases, attrs, **kwargs):
        attr_meta = attrs.get('Meta', None)
        if attr_meta and not getattr(attr_meta, 'abstract', None) and not getattr(attr_meta, 'proxy', None):
            data_name = "_".join(re.findall('[A-Z][a-z]*', name)).lower()
            class_file = sys.modules[attrs['__module__']].__file__

            if settings.APP_DIR in class_file:
                module = 'core'
            else:
                class_file = class_file.replace(settings.MODULE_BASE_PATH + '/', '')
                module = class_file.split('/')[1]

            attr_meta.db_table = "{}_{}".format(module, data_name)

        return super().__new__(cls, name, bases, attrs, **kwargs)


class BaseModelMixin(django.Model):

    created = django.DateTimeField(null = True, editable = False)
    updated = django.DateTimeField(null = True, editable = False)

    class Meta:
        abstract = True

    def initialize(self, command):
        return True

    def save(self, *args, **kwargs):
        if self.created is None:
            self.created = now()
        else:
            self.updated = now()

        with self.facade.thread_lock:
            super().save(*args, **kwargs)

    def save_related(self, provider, relation_values = None):
        if not relation_values:
            relation_values = {}

        relations = self.facade.get_relations()
        relation_values = {
            **provider.command.get_relations(self.facade),
            **relation_values
        }
        for field, value in relation_values.items():
            if value is not None:
                facade = provider.command.facade(
                    relations[field]['model'].facade.name
                )
                if relations[field]['multiple']:
                    provider.update_related(self, field, facade, value)
                else:
                    value = None if not value else value
                    provider.set_related(self, field, facade, value)

    @property
    def facade(self):
        return copy.deepcopy(self.__class__.facade)


class AppModel(
    BaseModelMixin,
    metaclass = CustomMetaModel
):
    class Meta:
        abstract = True
        facade_class = ModelFacade
        scope_process = 'pre'
        ordering = ['-created']
        search_fields = []
        ordering_fields = []
