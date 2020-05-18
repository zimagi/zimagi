from django.conf import settings
from django.db import models as django
from django.db.models.base import ModelBase
from django.db.models.manager import Manager
from django.utils.timezone import now

from .index import get_spec_key
from .facade import ModelFacade

import sys
import importlib
import re
import copy
import yaml
import logging


logger = logging.getLogger(__name__)


django.options.DEFAULT_NAMES += (
    'data_name',
    'meta_info',
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

def classify_parents(parent_classes):
    map = {}
    for parent in parent_classes:
        try:
            key = get_spec_key(parent.__module__)
        except Exception as e:
            key = 'base'

        map.setdefault(key, [])
        map[key].append(parent)
    return map

def classify_model(model_class_name):
    module_name = model_index().model_class_path.get(model_class_name, None)
    if module_name:
        return get_spec_key(module_name)
    return 'unknown'


class DatabaseAccessError(Exception):
    pass

class FacadeNotExistsError(Exception):
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
        spec_key = classify_model(name)
        parent_map = classify_parents(bases)
        meta_info = attrs.get('_meta_info', {})
        meta_bases = []

        logger.info("++++ Creating new model: {} <{}> {}".format(name, spec_key, bases))
        for field, value in meta_info.items():
            logger.debug(" init meta > {} - {}".format(field, value))

        for key in ('data', 'data_mixins', 'data_base', 'base'):
            for parent in parent_map.get(key, []):
                if key in ('base', 'data_base'):
                    if getattr(parent, 'Meta', None):
                        meta_bases.append(parent.Meta)

                for field, value in getattr(parent, '_meta_info', {}).items():
                    if field[0] != '_' and field not in ('abstract', 'db_table'):
                        meta_info.setdefault(field, value)

        if spec_key == 'data' and name.endswith('Override'):
            meta_info['abstract'] = False
        else:
            meta_info['abstract'] = True

        if not meta_info['abstract']:
            spec = model_index().spec['data'][meta_info['data_name']]
            app_name = spec.get('app', meta_info['data_name'])
            data_info = model_index().module_map['data'][app_name]
            meta_info['db_table'] = "{}_{}".format(data_info.module, meta_info['data_name'])

        attrs['Meta'] = type('Meta', tuple(meta_bases), meta_info)

        for field in dir(attrs['Meta']):
            if field[0] != '_':
                logger.debug(" final meta > {} - {}".format(field, getattr(attrs['Meta'], field)))

        return super().__new__(cls, name, bases, attrs, **kwargs)


    @property
    def facade_class(cls):
        class_name = re.sub(r'Override$', '', cls.__name__)
        module_name = model_index().model_class_path.get(class_name, None)
        module = importlib.import_module(module_name)
        facade_class_name = "{}Facade".format(class_name)
        override_class_name = "{}Override".format(facade_class_name)

        if getattr(module, override_class_name, None):
            facade_class = getattr(module, override_class_name)
        elif getattr(module, facade_class_name, None):
            facade_class = getattr(module, facade_class_name)
        else:
            raise FacadeNotExistsError("Neither dynamic or override facades exist for model {}".format(class_name))
        return facade_class

    @property
    def facade(cls):
        facade = None
        if not cls._meta.abstract:
            facade = model_index().model_class_facades.get(cls.__name__, None)
            if not facade:
                facade = cls.facade_class(cls)
                model_index().model_class_facades[cls.__name__] = facade
        return facade


class BaseMixin(
    django.Model,
    metaclass = BaseMetaModel
):
    class Meta:
        abstract = True

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
