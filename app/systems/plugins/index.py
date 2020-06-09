from django.conf import settings

from systems.command.parsers import python
from systems.models import index as model_index

import sys
import importlib
import imp
import inspect
import copy
import logging


logger = logging.getLogger(__name__)


class PluginNotExistsError(Exception):
    pass

class SpecNotFound(Exception):
    pass


def format_class_name(name, suffix = ''):
    return "".join([ component.title() for component in name.split('_') ]) + suffix.title()


def get_plugin_name(name, spec = None):
    if spec and 'class' in spec:
        return spec['class']
    return format_class_name(name.split('.')[-1])

def get_module_name(key, name, provider = None):
    if key == 'plugin_mixins':
        module_path = "plugins.mixins.{}".format(name)
    elif key == 'plugin':
        if provider:
            module_path = "plugins.{}.{}".format(name, provider)
        else:
            module_path = "plugins.{}".format(name)
    else:
        raise SpecNotFound("Key {} is not supported for plugin: {} ({})".format(key, name, provider))
    return module_path


class PluginGenerator(object):

    def __init__(self, key, name, **options):
        self.parser = python.PythonValueParser(None,
            settings = settings
        )
        self.key = key
        self.name = name
        self.name_list = self.name.split('.')
        self.provider = options.get('provider', None)
        self.full_spec = settings.MANAGER.index.spec

        self.parent_generator = options.get('parent', None)

        def parse_spec(spec, names):
            if not names:
                return spec

            name_component = names.pop(0)
            if 'subtypes' in spec:
                return parse_spec(spec['subtypes'].get(name_component, {}), names)
            return parse_spec(spec.get(name_component, {}), names)

        self.spec = self.parse_values(parse_spec(
            self.full_spec[self.key],
            copy.deepcopy(self.name_list)
        ))
        if not self.spec:
            raise SpecNotFound("Plugin specification does not exist for {}".format(name))

        if self.key == 'plugin_mixins':
            self.base_class_name = get_plugin_name(self.name, self.spec)
        elif self.parent_generator:
            self.base_class_name = format_class_name(self.name_list[-1], 'Provider')
        else:
            self.base_class_name = 'Provider' if self.provider else 'BaseProvider'

        self.dynamic_class_name = "{}Dynamic".format(self.base_class_name)
        self.ensure_exists = options.get('ensure_exists', False)

        provider = 'base' if not self.provider else self.provider
        module_info = self.get_module(self.name_list[0], provider)
        self.module = module_info['module']
        self.module_path = module_info['path']

        self.parents = None
        self.attributes = {}


    @property
    def klass(self):
        if getattr(self.module, self.base_class_name, None):
            klass = getattr(self.module, self.base_class_name)
        else:
            klass = getattr(self.module, self.dynamic_class_name, None)
            if klass and self.ensure_exists:
                klass = self.create_overlay(klass)

        return klass


    def get_provider(self, name, type_function):
        klass = self.parse_values(name)
        if isinstance(klass, str):
            klass = type_function(name)
        return klass


    def create_module(self, module_path):
        module = imp.new_module(module_path)
        sys.modules[module_path] = module
        return module

    def get_module(self, name, provider = None):
        module_path = get_module_name(self.key, name, provider)
        try:
            module = importlib.import_module(module_path)
        except ModuleNotFoundError:
            module = self.create_module(module_path)

        return {
            'module': module,
            'path': module_path
        }


    def init(self, attributes = None):
        self.init_parent()
        self.init_default_attributes(attributes)

    def init_parent(self):
        if inspect.isclass(self.spec.get('base', None)):
            self.parents = [ self.spec['base'] ]

        elif self.key == 'plugin_mixins':
            if 'base' not in self.spec or self.spec['base'] == 'base':
                from systems.plugins.base import BasePluginMixin
                self.parents = [ BasePluginMixin ]
            else:
                self.parents = [ ProviderMixin(self.spec['base']) ]
        else:
            if 'base' not in self.spec:
                self.spec['base'] = 'base'

            if self.parent_generator and self.spec['base'] in self.parent_generator.spec.get('subtypes', {}).keys():
                self.parents = [ BaseProvider(self.parent_generator.name, self.spec['base']) ]
            else:
                module_path = get_module_name(self.key, self.spec['base'])
                try:
                    module = importlib.import_module(module_path)
                    self.parents = [ getattr(module, 'BasePlugin') ]
                except Exception as e:
                    raise PluginNotExistsError("Base plugin {} does not exist: {}".format(self.spec['base'], e))

        if 'mixins' in self.spec:
            for mixin in ensure_list(self.spec['mixins']):
                self.parents.append(self.get_provider(mixin, ProviderMixin))


    def init_default_attributes(self, attributes):
        if attributes is None:
            attributes = {}
        self.attributes = attributes


    def attribute(self, name, value):
        self.attributes[name] = value

    def method(self, method, *spec_fields):
        if self._check_include(spec_fields):
            self.attributes[method.__name__] = method

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

        plugin = type(self.dynamic_class_name, tuple(parent_classes), self.attributes)
        plugin.__module__ = self.module_path
        setattr(self.module, self.dynamic_class_name, plugin)

        for parent in self.parents:
            parent.generate(plugin, self) # Allow parents to initialize class

        if self.ensure_exists:
            return self.create_overlay(plugin)
        return plugin

    def create_overlay(self, plugin):
        if getattr(self.module, self.base_class_name, None):
            return getattr(self.module, self.base_class_name)

        overlay_plugin = type(self.base_class_name, (plugin,), {})
        overlay_plugin.__module__ = self.module_path
        setattr(self.module, self.base_class_name, overlay_plugin)
        return overlay_plugin


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


def BasePlugin(name, ensure_exists = False):
    plugin = PluginGenerator('plugin', name,
        ensure_exists = ensure_exists
    )
    klass = plugin.klass
    if klass:
        return klass

    if not plugin.spec:
        raise PluginNotExistsError("Plugin {} does not exist yet".format(plugin.base_class_name))

    return _create_plugin(plugin)


def BaseProvider(plugin_name, provider_name):
    provider = PluginGenerator('plugin', plugin_name,
        provider = provider_name
    )
    klass = provider.klass
    if klass:
        return klass

    if not provider.spec:
        raise PluginNotExistsError("Plugin provider {} does not exist yet".format(provider.base_class_name))

    return _create_plugin(provider)


def ProviderMixin(name):
    mixin = PluginGenerator('plugin_mixins', name)
    klass = mixin.klass
    if klass:
        return klass

    if not mixin.spec:
        raise PluginNotExistsError("Plugin provider mixin {} does not exist yet".format(mixin.base_class_name))

    return _create_plugin(mixin)


def _create_plugin(plugin):
    plugin.init()

    if 'interface' in plugin.spec:
        for method, info in plugin.spec['interface'].items():
            def interface_method(self, *args, **kwargs):
                return None
            interface_method.__name__ = method
            plugin.method(interface_method)

    return plugin.create()


def display_plugin_info(klass, prefix = '', display_function = logger.info):
    display_function("{}{}".format(prefix, klass.__name__))
    for parent in klass.__bases__:
        display_plugin_info(parent, "{}  << ".format(prefix), display_function)

    display_function("{} properties:".format(prefix))
    for attribute in dir(klass):
        if not attribute.startswith('__') and not callable(getattr(klass, attribute)):
            display_function("{}  ->  {}".format(prefix, attribute))

    display_function("{} methods:".format(prefix))
    for attribute in dir(klass):
        if not attribute.startswith('__') and callable(getattr(klass, attribute)):
            display_function("{}  **  {}".format(prefix, attribute))
