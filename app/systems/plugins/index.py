from django.conf import settings

from systems.command.parsers import python
from systems.models import index as model_index

import sys
import importlib
import imp
import inspect
import logging


logger = logging.getLogger(__name__)


class PluginNotExistsError(Exception):
    pass


class PluginGenerator(object):

    def __init__(self, name, **options):
        self.parser = python.PythonValueParser(None,
            settings = settings
        )
        self.name = name

        self.full_spec = settings.MANAGER.index.spec
        self.spec = self.parse_values(self.full_spec['plugin'].get(name, {}))

        self.base_class_name = "BaseProvider"
        self.dynamic_class_name = "{}Dynamic".format(self.base_class_name)

        module_info = self.get_module(self.name)
        self.module = module_info['module']
        self.module_path = module_info['path']

        self.parent = None
        self.attributes = {}


    @property
    def klass(self):
        if getattr(self.module, self.base_class_name, None):
            klass = getattr(self.module, self.base_class_name)
        else:
            klass = getattr(self.module, self.dynamic_class_name, None)
            if klass:
                klass = self.create_overlay(klass)

        logger.debug("|> {} - plugins:{}".format(self.name, klass))
        return klass


    def create_module(self, module_path):
        module = imp.new_module(module_path)
        sys.modules[module_path] = module
        return module

    def get_module(self, name):
        module_path = "plugins.{}.base".format(name)
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
        from systems.plugins import base, data, meta

        if 'base' not in self.spec or self.spec['base'] == 'base':
            self.parent = base.BasePluginProvider
        elif self.spec['base'] == 'data':
            self.parent = data.DataPluginProvider
        elif self.spec['base'] == 'meta':
            self.parent = meta.MetaPluginProvider
        elif inspect.isclass(self.spec['base']):
            self.parent = self.spec['base']
        else:
            raise PluginNotExistsError("Base plugin {} does not exist".format(self.spec['base']))

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
        plugin = type(self.dynamic_class_name, (self.parent,), self.attributes)
        plugin.__module__ = self.module_path
        setattr(self.module, self.dynamic_class_name, plugin)
        return self.create_overlay(plugin)

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


def BasePlugin(name):
    plugin = PluginGenerator(name)
    klass = plugin.klass
    if klass:
        return klass

    if not plugin.spec:
        raise PluginNotExistsError("Plugin {} does not exist yet".format(plugin.base_class_name))

    return _create_plugin(plugin)


def _create_plugin(plugin):
    from systems.plugins import data
    plugin.init()

    def facade(self):
        return getattr(self.command, "_{}".format(plugin.spec['data']))

    if isinstance(plugin, data.DataPluginProvider) and 'data' in plugin.spec:
        plugin.attribute('facade', property(facade))

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
