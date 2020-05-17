from django.conf import settings
from django.db import models as django
from django.db.models.base import ModelBase
from django.db.models.manager import Manager
from django.utils.timezone import now

from .facade import ModelFacade

import sys
import inspect
import re
import copy


django.options.DEFAULT_NAMES += (
    'data_name',
    'abstract_original',
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

def model_index():
    return settings.MANAGER.index


class DatabaseAccessError(Exception):
    pass


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


class BaseMetaModel(ModelBase):

    def __new__(cls, name, bases, attrs, **kwargs):
        attr_meta = attrs.get('Meta', None)

        if attr_meta is None:
            for parent in reversed(bases):
                parent_meta = getattr(parent, 'Meta', None)
                if parent_meta:
                    attrs['Meta'] = copy.deepcopy(parent_meta)
                    attrs['Meta'].abstract = getattr(parent_meta, 'abstract_original', False)
                    attr_meta = attrs['Meta']
                    break
        else:
            # Django ModelBase resets the abstract flag to False after processing
            attr_meta.abstract_original = getattr(attr_meta, 'abstract', False)

        if attr_meta and not getattr(attr_meta, 'abstract', None) and not getattr(attr_meta, 'proxy', None):
            spec = model_index().spec['data'][attrs['Meta'].data_name]
            app_name = spec.get('app', attrs['Meta'].data_name)
            data_info = model_index().module_map['data'][app_name]

            data_name = "_".join(re.findall('[A-Z][a-z]*', name)).lower()
            attr_meta.db_table = "{}_{}".format(data_info.module, data_name)

        klass = super().__new__(cls, name, bases, attrs, **kwargs)
        # Django removes the passed in Meta class to default to a parent Meta unless abstract
        setattr(klass, 'Meta', attr_meta)
        return klass


    def __init__(cls, name, bases, attr):
        if not cls._meta.abstract:
            facade_class = cls._meta.facade_class

            if facade_class and inspect.isclass(facade_class):
                cls.facade = facade_class(cls)


class BaseModel(
    BaseModelMixin,
    metaclass = BaseMetaModel
):
    class Meta:
        abstract = True
        facade_class = ModelFacade
        scope_process = 'pre'
        ordering = ['-created']
        search_fields = []
        ordering_fields = []
