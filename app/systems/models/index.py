from django.conf import settings
from django.db import models as django
from django.db.models.fields.related import ManyToManyField
from django.contrib.postgres import fields as postgresql

from systems.models import fields
from utility.data import ensure_list
from utility.python import PythonParser

import os
import sys
import pathlib
import importlib
import imp
import inflect
import re
import copy
import oyaml
import logging


logger = logging.getLogger(__name__)


class ModelNotExistsError(Exception):
    pass

class SpecNotFound(Exception):
    pass


def get_dynamic_class_name(class_name):
    if check_dynamic(class_name):
        return class_name
    return "{}Dynamic".format(class_name)

def check_dynamic(class_name):
    return class_name.endswith('Dynamic')

def get_stored_class_name(class_name):
    return re.sub(r'Dynamic$', '', class_name)

def get_facade_class_name(class_name):
    if check_facade(class_name):
        return class_name
    return "{}Facade".format(class_name)

def check_facade(class_name):
    return class_name.endswith('Facade') or class_name.endswith('FacadeDynamic')


def get_model_name(name, spec = None):
    if spec and 'class' in spec:
        return spec['class']
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

        self.parser = PythonParser({
            'settings': settings,
            'django': django,
            'postgresql': postgresql,
            'zimagi': fields
        })
        self.pluralizer = inflect.engine()
        self.key = key
        self.name = name
        self.full_spec = settings.MANAGER.get_spec()

        try:
            self.spec = self.full_spec[key].get(name, None)
            self.app_name = self.spec.get('app', name)
        except Exception as e:
            raise ModelNotExistsError("Model specification {} {} does not exist".format(key, name))

        self.class_name = get_model_name(name, self.spec)
        self.dynamic_class_name = get_dynamic_class_name(self.class_name)
        self.facade_name = get_facade_class_name(self.class_name)
        self.dynamic_facade_name = get_dynamic_class_name(self.facade_name)

        self.base_model = options.get('base_model', base.BaseModel)
        self.ensure_exists = options.get('ensure_exists', False)

        self.ensure_model_files()
        module_info = self.get_module(self.app_name)
        self.module = module_info['module']
        self.module_path = module_info['path']

        self.parents = []
        self.attributes = {}
        self.facade_attributes = {}


    @property
    def klass(self):
        if getattr(self.module, self.class_name, None):
            klass = getattr(self.module, self.class_name)
        else:
            klass = getattr(self.module, self.dynamic_class_name, None)
            if klass and self.ensure_exists:
                klass = self.create_overlay(klass)

        return klass


    def ensure_facade(self):
        if not getattr(self.module, self.dynamic_facade_name, None):
            self.create_facade(self.dynamic_facade_name)


    def get_model(self, name, type_function):
        klass = self.parse_values(name)
        if isinstance(klass, str):
            klass = type_function(name)
        return klass

    def get_relation_class_name(self, name):
        klass = self.parse_values(name)
        if isinstance(klass, str):
            try:
                spec = self.full_spec['data'][klass]
                return "{}.{}".format(
                    spec.get('app', name),
                    get_model_name(klass, spec)
                )
            except Exception as e:
                logger.error(e)

            raise ModelNotExistsError("Base class for relation {} does not exist".format(klass))
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

    def init_parents(self):
        if 'extend' in self.spec:
            self.parents =  [ self.get_model(self.spec['extend'], Model) ]
        elif 'base' not in self.spec:
            self.parents = [ self.base_model ]
        else:
            if self.spec['base'] == 'resource':
                self.spec['base'] = 'id_resource' # Preserve backward compatibility

            self.parents = [ self.get_model(self.spec['base'], BaseModel) ]

        if 'mixins' in self.spec:
            for mixin in ensure_list(self.spec['mixins']):
                self.parents.append(self.get_model(mixin, ModelMixin))

    def init_default_attributes(self):
        meta_info = self.parse_values(copy.deepcopy(self.spec.get('meta', {})))

        if meta_info is None:
            meta_info = {}

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
        from systems.models.base import format_field_choices

        def get_display_method(field_name, color_type = None):

            def get_field_display(self, instance, value, short):
                if isinstance(value, (dict, list, tuple)):
                    value = oyaml.dump(value, indent = 2).strip()

                if color_type and value is not None:
                    return getattr(self, "{}_color".format(color_type))(value)
                return str(value)

            get_field_display.__name__ = "get_field_{}_display".format(field_name)
            return get_field_display

        fields = self.spec.get('fields', {})
        if fields is None:
            fields = {}

        for field_name, field_info in fields.items():
            if field_info is None:
                self.attribute(field_name, None)
            else:
                field_class = self.parse_values(field_info['type'])
                field_options = self.parse_values(field_info.get('options', {}))

                if 'relation' in field_info:
                    field_relation_class = self.get_relation_class_name(field_info['relation'])

                    if 'related_name' not in field_options:
                        if field_class is ManyToManyField:
                            field_options['related_name'] = "%(class)s_relations"
                        else:
                            field_options['related_name'] = "%(class)s_relation"

                    self.attribute(field_name, field_class(field_relation_class, **field_options))
                    color_type = field_info.get('color', 'relation')
                else:
                    if 'choices' in field_options:
                        field_options['choices'] = format_field_choices(field_options['choices'])

                    self.attribute(field_name, field_class(**field_options))
                    color_type = field_info.get('color', None)

                self.facade_method(get_display_method(field_name, color_type))

        if 'meta' in self.spec and self.spec['meta']:
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
            for field in [ field for field in spec_fields if field[0] != '-' ]:
                if field not in self.spec or self.spec[field] is None:
                    include = False
            if include:
                for field in [ field.lstrip('-') for field in spec_fields if field[0] == '-' ]:
                    if field in self.spec and self.spec[field] is not None:
                        include = False
        return include


    def create(self):
        self.ensure_facade()

        parent_classes = copy.deepcopy(self.parents)
        parent_classes.reverse()

        model = type(self.dynamic_class_name, tuple(parent_classes), self.attributes)
        model.__module__ = self.module_path
        setattr(self.module, self.dynamic_class_name, model)

        if self.ensure_exists:
            return self.create_overlay(model)
        return model

    def create_overlay(self, model):
        if getattr(self.module, self.class_name, None):
            return getattr(self.module, self.class_name)

        overlay_model = type(self.class_name, (model,), {
            '__module__': self.module_path
        })
        overlay_model.__module__ = self.module_path
        setattr(self.module, self.class_name, overlay_model)
        return overlay_model

    def create_facade(self, class_name):
        parent_classes = []
        for parent in reversed(self.parents):
            if getattr(parent, 'facade_class', None):
                parent_classes.append(parent.facade_class)

        if not parent_classes:
            from systems.models import facade
            parent_classes = [ facade.ModelFacade ]

        facade = type(class_name, tuple(parent_classes), self.facade_attributes)
        facade.__module__ = self.module_path
        setattr(self.module, class_name, facade)

        if 'triggers' in self.spec and settings.CLI_EXEC:
            triggers = self.spec['triggers']

            def clear(self, **filters):
                result = super(facade, self).clear(**filters)
                for trigger in ensure_list(triggers.get('save', [])):
                    Model('state').facade.store(trigger, { 'value': True })
                return result

            facade.clear = clear

        return facade


    def ensure_model_files(self):
        if self.key == 'data':
            data_info = settings.MANAGER.index.module_map['data'][self.app_name]
            model_dir = os.path.join(data_info.path, 'data', self.app_name)
            migration_dir = os.path.join(model_dir, 'migrations')

            pathlib.Path(migration_dir).mkdir(parents = True, exist_ok = True)

            model_file = os.path.join(model_dir, 'models.py')
            if not os.path.isfile(model_file):
                pathlib.Path(model_file).touch()

            migration_init_file = os.path.join(migration_dir, '__init__.py')
            if not os.path.isfile(migration_init_file):
                pathlib.Path(migration_init_file).touch()


    def parse_values(self, item):
        if isinstance(item, (list, tuple)):
            for index, element in enumerate(item):
                item[index] = self.parse_values(element)
        elif isinstance(item, dict):
            for name, element in item.items():
                item[name] = self.parse_values(element)
        elif isinstance(item, str):
            item = self.parser.parse(item)

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

def Model(name, ensure_exists = False):
    model = ModelGenerator('data', name,
        ensure_exists = ensure_exists
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

    def __str__(self):
        if 'display' in model.spec:
            display = model.spec['display'].replace('<', '{').replace('>', '}')
            return display.format(**self.__dict__)
        return "{}".format(getattr(self, self.facade.key(), self.get_id()))

    def get_id(self):
        return getattr(self, model.spec['id'], None)

    def get_id_fields(self):
        return ensure_list(model.spec['id_fields'])

    def key(self):
        return model.spec['key']

    def _ensure(self, command, reinit = False):
        if settings.CLI_EXEC:
            triggers = ensure_list(model.spec.get('triggers', {}).get('check', []))
            reinit_original = reinit
            if not reinit:
                for trigger in triggers:
                    reinit = command.get_state(trigger, True)
                    if reinit:
                        break
            if reinit or not triggers:
                self.ensure(command, reinit_original)
                for trigger in triggers:
                    command.set_state(trigger, False)
        else:
            self.ensure(command, reinit)

    def get_packages(self):
        return model.spec['packages']

    def check_api_enabled(self):
        return model.spec.get('api', True)

    def check_auto_create(self):
        return model.spec.get('auto_create', False)

    model.method(__str__)
    model.method(get_id, 'id', '-id_fields')
    model.method(get_id_fields, 'id_fields')
    model.facade_method(_ensure)
    model.facade_method(key, 'key')
    model.facade_method(get_packages, 'packages')
    model.facade_method(check_api_enabled)
    model.facade_method(check_auto_create)

    klass = model.create()

    if 'triggers' in model.spec and settings.CLI_EXEC:
        def save(self, *args, **kwargs):
            super(klass, self).save(*args, **kwargs)
            for trigger in ensure_list(model.spec['triggers'].get('save', [])):
                Model('state').facade.store(trigger, { 'value': True })

        klass.save = save

    return klass


def display_model_info(klass, prefix = '', display_function = logger.info):
    display_function("{}{}".format(prefix, klass.__name__))
    for parent in klass.__bases__:
        display_model_info(parent, "{}  << ".format(prefix), display_function)

    if getattr(klass, 'facade_class', None):
        display_model_info(klass.facade_class, "{}  ** ".format(prefix), display_function)

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

        if getattr(meta, 'scope', None):
            display_function("{} scope: {}".format(prefix, meta.scope))

        for field in meta.local_fields:
            related_info = ''
            if getattr(field, 'related_model', None):
                related_info = " -> {}".format(field.related_model)
            display_function("{} - field: {} <{}>{}".format(prefix, field.name, field.__class__.__name__, related_info))

        display_function("{} -> stored: {}".format(prefix, ", ".join(field_names)))
        display_function("{} -> dynamic: {}".format(prefix, ", ".join(dynamic_names)))
        display_function("{} -> relations: {}".format(prefix, ", ".join(relation_names)))
