from django.conf import settings
from django.db import models as django

from systems.command.parsers import python
from systems.models import fields
from utility.data import ensure_list

import os
import sys
import pathlib
import importlib
import imp
import copy
import logging


logger = logging.getLogger(__name__)


class ModelNotExistsError(Exception):
    pass


class ModelGenerator(object):

    def __init__(self, key, name, **options):
        self.parser = python.PythonValueParser(None, (settings, django, fields))
        self.key = key
        self.name = name
        self.full_spec = settings.MANAGER.index.spec
        self.spec = self.full_spec[key].get(name, None)
        self.app_name = self.spec.get('app', name)
        self.abstract = True

        if key == 'data':
            self.spec = self.spec.get(key, None)
            self.abstract = False

        self.dynamic_base = options.get('dynamic_base', False)
        self.class_name = self.get_model_name(name, self.spec)
        if self.dynamic_base:
            self.class_name = "{}Dynamic".format(self.class_name)

        self.ensure_model_files()
        module_info = self.get_module(self.app_name, self.spec)
        self.module = module_info['module']
        self.module_path = module_info['path']

        self.parents = []
        self.attributes = {}
        self.facade_attributes = {}


    @property
    def klass(self):
        if getattr(self.module, self.class_name, None):
            return getattr(self.module, self.class_name)
        return None


    def get_model_name(self, name, spec = None):
        if spec and 'model' in spec:
            return spec['model']
        return name.title()

    def get_model(self, name, type_function):
        klass = self.parse_values(name)
        if isinstance(klass, str):
            klass = type_function(name)
        return klass

    def get_class(self, name, key):
        klass = self.parse_values(name)
        if isinstance(klass, str):
            try:
                spec = self.full_spec[key][klass]
                if key == 'data':
                    module_name = spec.get('app', name)
                    spec = spec['data']
                else:
                    module_name = self.get_module(name, spec, key)['module'].__name__

                return "{}.{}".format(module_name, self.get_model_name(klass, spec))

            except Exception as e:
                pass

            raise ModelNotExistsError("Base class for key {} does not exist".format(klass))
        return klass.__name__


    def create_module(self, module_path):
        module = imp.new_module(module_path)
        sys.modules[module_path] = module
        return module

    def get_module(self, name, spec, key = None):
        data_spec = self.full_spec['data']

        if key is None:
            key = self.key

        if name in data_spec or key == 'data':
            module_path = "data.{}.models".format(name)
        else:
            module_path = "data.mixins.{}".format(name)

        try:
            module = importlib.import_module(module_path)
        except Exception:
            module = self.create_module(module_path)

        return {
            'module': module,
            'path': module_path
        }


    def init(self, **attributes):
        self.init_parents(**attributes)
        self.init_default_attributes(**attributes)
        self.init_fields(**attributes)

    def init_parents(self, **attributes):
        if 'base' not in self.spec:
            from data import base
            self.parents = [ attributes.get('base_model', base.BaseModel) ]
        else:
            self.parents = [ self.get_model(self.spec['base'], BaseModel) ]

        if 'mixins' in self.spec:
            for mixin in ensure_list(self.spec['mixins']):
                self.parents.append(self.get_model(mixin, ModelMixin))

    def init_default_attributes(self, **attributes):
        meta_info = self.parse_values(copy.deepcopy(self.spec.get('meta', {})))

        if self.abstract:
            meta_info['abstract'] = True

        meta_info['data_name'] = self.name
        meta_info['facade_class'] = self.create_facade()

        self.attributes = {
            '__module__': self.module_path,
            'Meta': type('Meta',
                (getattr(self.parents[0], 'Meta', object),),
                meta_info
            )
        }

    def init_fields(self, **attributes):
        for field_name, field_info in self.spec.get('fields', {}).items():
            if field_info is None:
                self.attribute(field_name, None)
            else:
                field_class = self.parse_values(field_info['type'])
                field_options = self.parse_values(field_info.get('options', {}))

                if 'relation' in field_info:
                    field_relation_class = self.get_class(field_info['relation'], 'data')
                    self.attribute(field_name, field_class(field_relation_class, **field_options))
                else:
                    self.attribute(field_name, field_class(**field_options))


    def attribute(self, name, value):
        self.attributes[name] = value

    def facade_attribute(self, name, value):
        self.facade_attributes[name] = value

    def method(self, method, *spec_fields):
        if self._check_include(spec_fields):
            self.attributes[method.__name__] = method

    def facade_method(self, method, *spec_fields):
        if self._check_include(spec_fields):
            self.facade_attributes[method.__name__] = method

    def _check_include(self, spec_fields):
        include = True
        if spec_fields:
            for field in spec_fields:
                if field not in self.spec:
                    include = False
        return include


    def create(self):
        parent_classes = copy.deepcopy(self.parents)
        parent_classes.reverse()

        model = type(self.class_name, tuple(parent_classes), self.attributes)
        model.__module__ = self.module.__name__
        setattr(self.module, self.class_name, model)
        return model

    def create_facade(self):
        facade_class_name = "{}Facade".format(self.class_name)
        parent_classes = []

        for parent in reversed(self.parents):
            if getattr(parent, 'Meta', None) and getattr(parent.Meta, 'facade_class', None):
                parent_classes.append(parent.Meta.facade_class)

        if not parent_classes:
            from systems.models import facade
            parent_classes = [ facade.ModelFacade ]

        facade = type(facade_class_name, tuple(parent_classes), self.facade_attributes)
        facade.__module__ = self.module.__name__
        setattr(self.module, facade_class_name, facade)
        return facade


    def ensure_model_files(self):
        if not self.abstract:
            data_info = settings.MANAGER.index.module_map['data'][self.app_name]
            model_dir = os.path.join(data_info.path, 'data', self.app_name)
            migration_dir = os.path.join(model_dir, 'migrations')

            pathlib.Path(migration_dir).mkdir(mode = 0o755, parents = True, exist_ok = True)
            pathlib.Path(os.path.join(model_dir, 'models.py')).touch(mode = 0o644, exist_ok = True)
            pathlib.Path(os.path.join(migration_dir, '__init__.py')).touch(mode = 0o644, exist_ok = True)


    def parse_values(self, item):
        if isinstance(item, (list, tuple)):
            for index, element in enumerate(item):
                item[index] = self.parse_values(element)
        elif isinstance(item, dict):
            for name, element in item.items():
                item[name] = self.parse_values(element)
        elif isinstance(item, str):
            item = self.parser.interpolate(item)

        return item


def BaseModel(name, dynamic_base = False):
    return AbstractModel('data_base', name,
        dynamic_base = dynamic_base
    )

def BaseModelFacade(name, dynamic_base = False):
    model = BaseModel(name, dynamic_base = dynamic_base)
    return model.Meta.facade_class

def ModelMixin(name, dynamic_base = False):
    return AbstractModel('data_mixins', name,
        dynamic_base = dynamic_base,
        base_model = django.Model
    )

def ModelMixinFacade(name, dynamic_base = False):
    mixin = ModelMixin(name, dynamic_base = dynamic_base)
    return mixin.Meta.facade_class


def AbstractModel(key, name, **options):
    model = ModelGenerator(key, name, **options)
    if model.klass:
        return model.klass

    if not model.spec:
        raise ModelNotExistsError("Abstract model {} does not exist yet".format(model.class_name))

    return _create_model(model, options)

def Model(name, **options):
    model = ModelGenerator('data', name, **options)
    if model.klass:
        return model.klass

    if not model.spec:
        raise ModelNotExistsError("Model {} does not exist yet".format(model.class_name))

    return _create_model(model, options)

def ModelFacade(name, dynamic_base = False):
    model = Model(name, dynamic_base = dynamic_base)
    return model.Meta.facade_class


def _create_model(model, options):
    model.init(**options)
    _include_base_methods(model)
    return model.create()

def _include_base_methods(model):

    def __str__(self):
        return "{} <{}>".format(name, model.class_name)

    def get_id(self):
        return getattr(self, model.spec['id'])

    def get_id_fields(self):
        return ensure_list(model.spec['id_fields'])

    def key(self):
        return model.spec['key']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        for trigger in ensure_list(model.spec['triggers']):
            Model('state').facade.store(trigger, value = True)

    def get_packages(self):
        return model.spec['packages']

    model.method(__str__)
    model.method(get_id, 'id')
    model.method(get_id_fields, 'id_fields')
    model.method(save, 'triggers')
    model.facade_method(key, 'key')
    model.facade_method(get_packages, 'packages')
