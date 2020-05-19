from django.conf import settings
from django.db import models as django
from django.db.models.fields.related import ManyToManyField

from systems.command.parsers import python
from systems.models import fields
from utility.data import ensure_list

import os
import sys
import pathlib
import importlib
import imp
import inspect
import inflect
import re
import copy
import json
import oyaml
import logging


logger = logging.getLogger(__name__)


class ModelNotExistsError(Exception):
    pass

class SpecNotFound(Exception):
    pass


def get_model_name(name, spec = None):
    if spec and 'model' in spec:
        return spec['model']
    return name.title()

def get_module_name(key, name):
    if key == 'data_base':
        module_path = "data.base.{}".format(name)
    elif key == 'data_mixins':
        module_path = "data.mixins.{}".format(name)
    elif key == 'data':
        module_path = "data.{}.models".format(name)
    else:
        raise SpecNotFound("Key {} is not supported for data: {}".format(key, name))
    return module_path

def get_spec_key(module_name):
    if re.match(r'^data.base.[^\.]+$', module_name):
        key = 'data_base'
    elif re.match(r'^data.mixins.[^\.]+$', module_name):
        key = 'data_mixins'
    elif re.match(r'^data.[^\.]+.models$', module_name):
        key = 'data'
    else:
        raise SpecNotFound("Key for module {} was not found for data".format(module_name))
    return key


class ModelGenerator(object):

    def __init__(self, key, name, **options):
        from systems.models import base

        self.parser = python.PythonValueParser(None, (settings, django, fields))
        self.pluralizer = inflect.engine()
        self.key = key
        self.name = name
        self.full_spec = settings.MANAGER.index.spec
        self.spec = self.full_spec[key].get(name, None)
        self.app_name = self.spec.get('app', name)

        if key == 'data':
            self.spec = self.spec.get(key, None)

        self.class_name = self.get_model_name(name, self.spec)
        self.base_model = options.get('base_model', base.BaseModel)
        self.ensure_override = options.get('ensure_override', False)

        self.ensure_model_files()
        module_info = self.get_module(self.app_name)
        self.module = module_info['module']
        self.module_path = module_info['path']

        self.parents = []
        self.attributes = {}
        self.facade_attributes = {}


    @property
    def klass(self):
        override_class_name = "{}Override".format(self.class_name)
        klass = getattr(self.module, self.class_name, None)

        if klass and self.ensure_override:
            klass = self.create_override(klass)
        elif getattr(self.module, override_class_name, None):
            klass = getattr(self.module, override_class_name)

        logger.debug("|> {} - {}:{}".format(self.name, self.key, klass))
        return klass


    def ensure_facade(self):
        facade_class_name = "{}Facade".format(self.class_name)
        override_class_name = "{}Override".format(facade_class_name)

        if getattr(self.module, override_class_name, None):
            return getattr(self.module, override_class_name)
        elif getattr(self.module, facade_class_name, None):
            return getattr(self.module, facade_class_name)

        self.create_facade(facade_class_name)


    def get_model_name(self, name, spec = None):
        return get_model_name(name, spec)

    def get_model(self, name, type_function):
        klass = self.parse_values(name)
        if isinstance(klass, str):
            klass = type_function(name)
        return klass

    def get_class_name(self, name, key):
        klass = self.parse_values(name)
        if isinstance(klass, str):
            try:
                spec = self.full_spec[key][klass]
                module = self.get_module(name, key)['module'].__name__
                if key == 'data':
                    module_path = spec.get('app', name)
                    spec = spec['data']
                    model_name = "{}Override".format(self.get_model_name(klass, spec))
                else:
                    module_path = module.__name__
                    model_name = self.get_model_name(klass, spec)
                    model_override_name = "{}Override".format(model_name)
                    if getattr(module, model_override_name, None):
                        model_name = model_override_name

                return "{}.{}".format(module_path, model_name)

            except Exception as e:
                logger.error(e)

            raise ModelNotExistsError("Base class for key {} does not exist".format(klass))
        return klass.__name__


    def create_module(self, module_path):
        module = imp.new_module(module_path)
        sys.modules[module_path] = module
        return module

    def get_module(self, name, key = None):
        if key is None:
            key = self.key

        module_path = get_module_name(key, name)
        try:
            module = importlib.import_module(module_path)
        except ModuleNotFoundError:
            module = self.create_module(module_path)

        return {
            'module': module,
            'path': module_path
        }


    def init(self):
        self.init_parents()
        self.init_default_attributes()
        self.init_fields()
        self.ensure_facade()

    def init_parents(self):
        if 'base' not in self.spec:
            self.parents = [ self.base_model ]
        else:
            self.parents = [ self.get_model(self.spec['base'], BaseModel) ]

        if 'mixins' in self.spec:
            for mixin in ensure_list(self.spec['mixins']):
                self.parents.append(self.get_model(mixin, ModelMixin))

    def init_default_attributes(self):
        meta_info = self.parse_values(copy.deepcopy(self.spec.get('meta', {})))

        meta_info['data_name'] = self.name

        if 'verbose_name' not in meta_info:
            meta_info['verbose_name'] = re.sub(r'_+', ' ', self.name).strip()

        if 'verbose_name_plural' not in meta_info:
            meta_info['verbose_name_plural'] = self.pluralizer.plural(meta_info['verbose_name'])

        self.attributes = {
            '__module__': self.module_path,
            '_meta_info': meta_info
        }

    def init_fields(self, **attributes):

        def get_display_method(field_name, color = None):

            def get_field_display(self, instance, value, short):
                value = json.loads(value)
                if isinstance(value, (dict, list, tuple)):
                    value = oyaml.dump(value, indent = 2).strip()

                if color and value is not None:
                    return getattr(self, "{}_color".format(color))(value)
                return str(value)

            get_field_display.__name__ = "get_field_{}_display".format(field_name)
            return get_field_display

        for field_name, field_info in self.spec.get('fields', {}).items():
            if field_info is None:
                self.attribute(field_name, None)
            else:
                field_class = self.parse_values(field_info['type'])
                field_options = self.parse_values(field_info.get('options', {}))

                if 'relation' in field_info:
                    field_relation_class = self.get_class_name(field_info['relation'], 'data')

                    if 'related_name' not in field_options:
                        if field_class is ManyToManyField:
                            field_options['related_name'] = "%(class)s_relations"
                        else:
                            field_options['related_name'] = "%(class)s_relation"

                    self.attribute(field_name, field_class(field_relation_class, **field_options))
                    color = field_info.get('color', 'relation')
                else:
                    self.attribute(field_name, field_class(**field_options))
                    color = field_info.get('color', None)

                self.facade_method(get_display_method(field_name, color))

        if 'meta' in self.spec:
            for field_name in self.spec['meta'].get('dynamic_fields', []):
                self.facade_method(get_display_method(field_name, 'dynamic'))


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
        model.__module__ = self.module_path
        setattr(self.module, self.class_name, model)

        if self.ensure_override:
            return self.create_override(model)
        return model

    def create_override(self, model):
        override_class_name = "{}Override".format(self.class_name)

        if getattr(self.module, override_class_name, None):
            return getattr(self.module, override_class_name)

        override_model = type(override_class_name, (model,), {
            '__module__': self.module_path
        })
        override_model.__module__ = self.module_path
        setattr(self.module, override_class_name, override_model)
        return override_model

    def create_facade(self, class_name):
        parent_classes = []

        for parent in reversed(self.parents):
            if getattr(parent, 'facade_class', None):
                parent_classes.append(parent.facade_class)

        if not parent_classes:
            from systems.models import facade
            parent_classes = [ facade.ModelFacade ]

        facade = type(class_name, tuple(parent_classes), self.facade_attributes)
        facade.__module__ = self.module.__name__
        setattr(self.module, class_name, facade)
        return facade


    def ensure_model_files(self):
        if self.key == 'data':
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


def BaseModel(name):
    return AbstractModel('data_base', name)

def BaseModelFacade(name):
    model = BaseModel(name)
    return model.facade_class

def ModelMixin(name):
    from systems.models import base
    return AbstractModel('data_mixins', name,
        base_model = base.BaseMixin
    )

def ModelMixinFacade(name):
    mixin = ModelMixin(name)
    return mixin.facade_class


def DerivedAbstractModel(module, model_name, **fields):
    if isinstance(module, str):
        module = importlib.import_module(module)

    model = getattr(module, model_name)
    if not model:
        raise ModelNotExistsError("Model {} does not exist in module {}".format(model_name, module.__name__))

    attributes = dict(model.__dict__)
    for field in model._meta.local_fields:
        attributes[field.name] = field

    for field, value in fields.items():
        attributes[field] = value

    attributes.pop('_meta')
    if 'Meta' in attributes:
        attributes["Meta"].abstract = True

    model = type(model_name, model.__bases__, attributes)
    setattr(module, model_name, model)
    return model

def AbstractModel(key, name, **options):
    model = ModelGenerator(key, name, **options)
    klass = model.klass
    if klass:
        return klass

    if not model.spec:
        raise ModelNotExistsError("Abstract model {} does not exist yet".format(model.class_name))

    return _create_model(model)

def Model(name, ensure_override = False):
    model = ModelGenerator('data', name,
        ensure_override = ensure_override
    )
    klass = model.klass
    if klass:
        return klass

    if not model.spec:
        raise ModelNotExistsError("Model {} does not exist yet".format(model.class_name))

    return _create_model(model)

def ModelFacade(name):
    model = Model(name)
    return model.facade_class


def _create_model(model):
    model.init()
    _include_base_methods(model)
    return model.create()

def _include_base_methods(model):

    def __str__(self):
        return "{} <{}>".format(name, model.class_name)

    def get_id(self):
        return getattr(self, model.spec['id'])

    def get_id_fields(self):
        return ensure_list(model.spec.get('id_fields', []))

    def key(self):
        return model.spec['key']

    def _ensure(self, command, reinit = False):
        reinit_original = reinit
        if not reinit:
            for trigger in ensure_list(model.spec['triggers']):
                reinit = command.get_state(trigger, True)
                if reinit:
                    break
        if reinit:
            self.ensure(command, reinit_original)
            for trigger in ensure_list(model.spec['triggers']):
                Model('state').facade.store(trigger, value = False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        for trigger in ensure_list(model.spec['triggers']):
            Model('state').facade.store(trigger, value = True)

    def clear(self, **filters):
        result = super().clear(**filters)
        for trigger in ensure_list(model.spec['triggers']):
            Model('state').facade.store(trigger, value = True)
        return result

    def get_packages(self):
        return model.spec['packages']

    model.method(__str__)
    model.method(get_id, 'id')
    model.method(get_id_fields)
    model.method(save, 'triggers')
    model.facade_method(_ensure)
    model.facade_method(clear, 'triggers')
    model.facade_method(key, 'key')
    model.facade_method(get_packages, 'packages')


def display_model_info(klass, prefix = '', display_function = logger.info):
    display_function("{}{}".format(prefix, klass.__name__))
    for parent in klass.__bases__:
        display_model_info(parent, "{}  << ".format(prefix))

    if getattr(klass, 'facade_class', None):
        display_model_info(klass.facade_class, "{}  ** ".format(prefix))

    if getattr(klass, '_meta', None):
        meta = klass._meta
        field_names = []
        for field in meta.fields:
            field_names.append(field.name)

        dynamic_names = []
        if getattr(meta, 'dynamic_fields', None):
            dynamic_names = meta.dynamic_fields

        relation_names = []
        for field in meta.get_fields():
            if field.name not in field_names:
                relation_names.append(field.name)

        display_function("{} name: {}".format(prefix, meta.verbose_name))
        display_function("{} plural: {}".format(prefix, meta.verbose_name_plural))

        if getattr(meta, 'db_table', None):
            display_function("{} db table: {}".format(prefix, meta.db_table))

        if getattr(meta, 'pk', None):
            display_function("{} pk: {}".format(prefix, meta.pk.name))
        else:
            display_function("{} pk: NOT DEFINED".format(prefix))

        if getattr(meta, 'scope_process', None):
            display_function("{} scope process: {}".format(prefix, meta.scope_process))

        if getattr(meta, 'scope', None):
            display_function("{} scope: {}".format(prefix, meta.scope))

        if getattr(meta, 'relation', None):
            display_function("{} relations: {}".format(prefix, meta.relation))

        for field in meta.local_fields:
            related_info = ''
            if getattr(field, 'related_model', None):
                related_info = " -> {}".format(field.related_model)
            display_function("{} - field: {} <{}>{}".format(prefix, field.name, field.__class__.__name__, related_info))

        display_function("{} -> stored: {}".format(prefix, ", ".join(field_names)))
        display_function("{} -> dynamic: {}".format(prefix, ", ".join(dynamic_names)))
        display_function("{} -> relations: {}".format(prefix, ", ".join(relation_names)))
