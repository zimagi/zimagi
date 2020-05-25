from django.conf import settings

from systems.models import index as model_index
from systems.command.parsers import python
from utility.data import ensure_list

import sys
import importlib
import imp
import re
import copy
import yaml
import logging


logger = logging.getLogger(__name__)


class CommandNotExistsError(Exception):
    pass

class SpecNotFound(Exception):
    pass

class ParseMethodNotSupportedError(Exception):
    pass

class ParseError(Exception):
    pass

class CallbackNotExistsError(Exception):
    pass


def get_dynamic_class_name(class_name):
    if check_dynamic(class_name):
        return class_name
    return "{}Dynamic".format(class_name)

def check_dynamic(class_name):
    return class_name.endswith('Dynamic')

def get_stored_class_name(class_name):
    return re.sub(r'Dynamic$', '', class_name)


def get_command_name(name, spec = None):
    if spec and 'class' in spec:
        return spec['class']
    return name.title()

def get_module_name(key, name):
    if key == 'command_base':
        module_path = "command.base.{}".format(name)
    elif key == 'command_mixins':
        module_path = "command.mixins.{}".format(name)
    elif key == 'data':
        module_path = "data.{}.commands".format(name)
    else:
        raise SpecNotFound("Key {} is not supported for command: {}".format(key, name))
    return module_path

def get_spec_key(module_name):
    if re.match(r'^command.base.[^\.]+$', module_name):
        key = 'command_base'
    elif re.match(r'^command.mixins.[^\.]+$', module_name):
        key = 'command_mixins'
    elif re.match(r'^data.[^\.]+.commands$', module_name):
        key = 'data'
    else:
        raise SpecNotFound("Key for module {} was not found for command".format(module_name))
    return key


class CommandGenerator(object):

    def __init__(self, key, name, **options):
        self.parser = python.PythonValueParser(None,
            settings = settings
        )
        self.key = key
        self.name = name
        self.full_spec = settings.MANAGER.index.spec
        self.spec = self.full_spec[key].get(name, None)
        self.app_name = self.spec.get('app', name)

        if key == 'data':
            self.spec = self.spec.get('command', None)

        self.spec = self.parse_values(self.spec)
        self.class_name = get_command_name(name, self.spec)
        self.dynamic_class_name = get_dynamic_class_name(self.class_name)

        if options.get('base_command', None):
            self.base_command = options['base_command']
        else:
            from systems.command import action
            self.base_command = action.ActionCommand

        self.ensure_exists = options.get('ensure_exists', False)

        module_info = self.get_module(self.app_name)
        self.module = module_info['module']
        self.module_path = module_info['path']

        self.parents = []
        self.attributes = {}


    @property
    def klass(self):
        if getattr(self.module, self.class_name, None):
            klass = getattr(self.module, self.class_name)
        else:
            klass = getattr(self.module, self.dynamic_class_name, None)
            if klass and self.ensure_exists:
                klass = self.create_overlay(klass)

        logger.debug("|> {} - {}:{}".format(self.name, self.key, klass))
        return klass


    def get_command(self, name, type_function):
        klass = self.parse_values(name)
        if isinstance(klass, str):
            klass = type_function(name)
        return klass


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


    def init(self, attributes = None):
        self.init_parents()
        self.init_default_attributes(attributes)

    def init_parents(self):
        if 'base' not in self.spec:
            self.parents = [ self.base_command ]
        else:
            self.parents = [ self.get_command(self.spec['base'], Command) ]

        if 'mixins' in self.spec:
            for mixin in ensure_list(self.spec['mixins']):
                self.parents.append(self.get_command(mixin, CommandMixin))

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

        command = type(self.dynamic_class_name, tuple(parent_classes), self.attributes)
        command.__module__ = self.module_path
        setattr(self.module, self.dynamic_class_name, command)

        if self.ensure_exists:
            return self.create_overlay(command)
        return command

    def create_overlay(self, command):
        if getattr(self.module, self.class_name, None):
            return getattr(self.module, self.class_name)

        overlay_command = type(self.class_name, (command,), {})
        overlay_command.__module__ = self.module_path
        setattr(self.module, self.class_name, overlay_command)
        return overlay_command


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


def BaseCommand(name):
    return _Command('command_base', name)

def Command(name, ensure_exists = False):
    # Command Registry Lookup
    return _Command('data', name,
        ensure_exists = ensure_exists
    )


def CommandMixin(name):
    from systems.command.mixins import base
    mixin = CommandGenerator('command_mixins', name,
        base_command = base.BaseMixin
    )
    klass = mixin.klass
    if klass:
        return klass

    if not mixin.spec:
        raise CommandNotExistsError("Command mixin {} does not exist yet".format(mixin.class_name))

    return _create_command_mixin(mixin)


def _Command(key, name, **options):
    command = CommandGenerator(key, name, **options)
    klass = command.klass
    if klass:
        return klass

    if not command.spec:
        raise CommandNotExistsError("Command {} does not exist yet".format(command.class_name))

    return _create_command(command)


def _get_command_methods(command):
    parse_methods = {}

    # BaseCommand method overrides

    def __str__(self):
        return "{} <{}>".format(name, command.class_name)

    def get_priority(self):
        return command.spec['priority']

    def server_enabled(self):
        return command.spec['server_enabled']

    def remote_exec(self):
        return command.spec['remote_exec']

    def groups_allowed(self):
        return ensure_list(command.spec['groups_allowed'])

    if 'parameters' in command.spec:
        for name, info in command.spec['parameters'].items():
            parse_methods[name] = _get_parse_method(name, info)
            command.method(parse_methods[name])
            command.attribute(name, _get_accessor_method(name, info))

    def interpolate_options(self):
        return command.spec['interpolate_options']

    def parse_passthrough(self):
        return command.spec['parse_passthrough']

    def parse(self):
        if isinstance(command.spec['parse'], (str, list, tuple)):
            for name in ensure_list(command.spec['parse']):
                getattr(self, "parse_{}".format(name))()

        elif isinstance(command.spec['parse'], dict):
            for name, options in command.spec['parse'].items():
                parse_method = getattr(self, "parse_{}".format(name))

                if options is None:
                    parse_method()
                elif isinstance(options, (str, list, tuple)):
                    parse_method(*ensure_list(options))
                elif isinstance(options, dict):
                    parse_method(**options)
                else:
                    raise ParseError("Command parameter parse options {} not recognized: {}".format(options, command.spec['parse']))
        else:
            raise ParseError("Command parameter parse list not recognized: {}".format(command.spec['parse']))

    def confirm(self):
        if command.spec['confirm']:
            self.confirmation()

    # ActionCommand method overrides

    def display_header(self):
        return command.spec['display_header']

    command.method(__str__)
    command.method(get_priority, 'priority')
    command.method(server_enabled, 'server_enabled')
    command.method(remote_exec, 'remote_exec')
    command.method(groups_allowed, 'groups_allowed')
    command.method(interpolate_options, 'interpolate_options')
    command.method(parse_passthrough, 'parse_passthrough')
    command.method(parse, 'parse')
    command.method(confirm, 'confirm')
    command.method(display_header, 'display_header')


def _create_command(command):
    command.init()
    _get_command_methods(command)
    return command.create()

def _create_command_mixin(mixin):
    schema_info = {}

    if 'meta' in mixin.spec:
        for name, info in mixin.spec['meta'].items():
            schema_info[name] = {}

            if 'data' in info and info['data'] is not None:
                schema_info[name]['model'] = model_index.Model(info['data'])

            if 'provider' in info:
                schema_info[name]['provider'] = info['provider']
            if 'provider_config' in info:
                schema_info[name]['provider_config'] = info['provider_config']

            if 'name_default' in info:
                schema_info[name]['name_default'] = info['name_default']
            if 'default' in info:
                schema_info[name]['default'] = info['default']

    mixin.init({ 'schema': schema_info })
    _get_command_methods(mixin)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, info in schema_info.items():
            if 'model' in info:
                priority = 50
                if 'priority' in mixin.spec['meta'][name]:
                    priority = mixin.spec['meta'][name]['priority']
                self.facade_index["{:02d}_{}".format(priority, name)] = self.facade(info['model'].facade)

    mixin.method(__init__, 'meta')
    return mixin.create()


def _get_parse_method(method_base_name, method_info):
    method_type = method_info.get('parser', 'variable')
    method = None

    if 'default_callback' in method_info:
        default_callback = getattr(self, method_info['default_callback'], None)
        if default_callback is None:
            raise CallbackNotExistsError("Command parameter default callback {} does not exist".format(default_callback))
        default_value = default_callback()
    else:
        default_value = method_info.get('default', None)

    if method_type == 'flag':
        def parse_flag(self,
            flag = method_info.get('flag', "--{}".format(method_base_name)),
            help_text = method_info.get('help', '')
        ):
            self.parse_flag(method_base_name,
                flag = flag,
                help_text = help_text
            )
        method = parse_flag

    elif method_type == 'variable':
        def parse_variable(self,
            optional = method_info.get('optional', "--{}".format(method_base_name)),
            help_text = method_info.get('help', ''),
            value_label = method_info.get('value_label', None)
        ):
            self.parse_variable(method_base_name,
                optional = optional,
                type = method_info.get('type', 'str'),
                help_text = "{} (default: {})".format(help_text, default_value),
                value_label = value_label,
                choices = method_info.get('choices', None),
                default = default_value
            )
        method = parse_variable

    elif method_type == 'variables':
        def parse_variables(self,
            optional = method_info.get('optional', "--{}".format(method_base_name)),
            help_text = method_info.get('help', ''),
            value_label = method_info.get('value_label', None)
        ):
            self.parse_variables(method_base_name,
                optional = optional,
                type = method_info.get('type', 'str'),
                help_text = "{} (default: {})".format(help_text, default_value),
                value_label = value_label,
                default = default_value
            )
        method = parse_variables

    elif method_type == 'fields':
        def parse_fields(self,
            optional = method_info.get('optional', False),
            help_callback = method_info.get('help_callback', None),
            callback_args = method_info.get('callback_args', None),
            callback_options = method_info.get('callback_options', None)
        ):
            facade = False
            if method_info.get('data', None):
                facade = model_index.Model(method_info['data']).facade

            self.parse_fields(facade, method_base_name,
                optional = optional,
                help_callback = help_callback,
                callback_args = callback_args,
                callback_options = callback_options
            )
        method = parse_fields

    else:
        raise ParseMethodNotSupportedError("Command parameter type {} is not currently supported".format(method_type))

    method.__name__ = "parse_{}".format(method_base_name)
    return method

def _get_accessor_method(method_base_name, method_info):
    def accessor(self):
        value = self.options.get(method_base_name, None)
        if value is None:
            value = method_info.get('default', None)

        if method_info['parser'] == 'variables':
            value = ensure_list(value) if value else []
        elif method_info['parser'] == 'fields':
            value = value if value else {}

        if 'postprocessor' in method_info:
            postprocessor = getattr(self, method_info['postprocessor'], None)
            if postprocessor is None:
                raise CallbackNotExistsError("Command parameter postprocessor {} does not exist".format(postprocessor))

            if value is not None:
                value = postprocessor(value)

        return value

    accessor.__name__ = method_base_name
    return property(accessor)


def display_command_info(klass, prefix = '', display_function = logger.info):
    display_function("{}{}".format(prefix, klass.__name__))
    for parent in klass.__bases__:
        display_command_info(parent, "{}  << ".format(prefix), display_function)

    display_function("{} properties:".format(prefix))
    for attribute in dir(klass):
        if not attribute.startswith('__') and not callable(getattr(klass, attribute)):
            display_function("{}  ->  {}".format(prefix, attribute))

    display_function("{} methods:".format(prefix))
    for attribute in dir(klass):
        if not attribute.startswith('__') and callable(getattr(klass, attribute)):
            display_function("{}  **  {}".format(prefix, attribute))
