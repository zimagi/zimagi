from django.conf import settings

from systems.models import index as model_index
from systems.commands.factory import resource
from utility.data import ensure_list
from utility.python import PythonParser

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


def get_command_name(key, name, spec = None):
    if key != 'command' and spec and 'class' in spec:
        return spec['class']
    return name.split('.')[-1].title()

def get_module_name(key, name):
    if key == 'command_base':
        module_path = "commands.base.{}".format(name)
    elif key == 'command_mixins':
        module_path = "commands.mixins.{}".format(name)
    elif key == 'command':
        module_path = "commands.{}".format(name)
    else:
        raise SpecNotFound("Key {} is not supported for command: {}".format(key, name))
    return module_path

def get_spec_key(module_name):
    if re.match(r'^commands.base.[^\.]+$', module_name):
        key = 'command_base'
    elif re.match(r'^commands.mixins.[^\.]+$', module_name):
        key = 'command_mixins'
    elif re.match(r'^commands.[a-z\_\.]+$', module_name):
        key = 'command'
    else:
        raise SpecNotFound("Key for module {} was not found for command".format(module_name))
    return key


def generate_command_tree(spec, name = 'root', parent_command = None, lookup_path = ''):
    from systems.commands.router import RouterCommand
    command = RouterCommand(name, parent_command, spec.get('priority', 1))

    if name != 'root':
        if 'base' in spec:
            if 'resource' in spec:
                _generate_resource_commands(command, name, spec)
            else:
                return Command(lookup_path)

    for sub_name, sub_spec in spec.items():
        if isinstance(sub_spec, dict):
            subcommand = generate_command_tree(
                sub_spec,
                sub_name,
                command,
                "{}.{}".format(lookup_path, sub_name).strip('.')
            )
            if subcommand:
                command[sub_name] = subcommand

    return command if not command.is_empty else None


def find_command(full_name, parent = None):
    from systems.commands.router import RouterCommand

    def find(components, command, parents = None):
        if not parents:
            parents = []

        name = components.pop(0)

        if isinstance(command, RouterCommand):
            subcommand = command.get(name)

            if command.name != 'root':
                parents.append(command)

            if subcommand:
                if len(components):
                    command = find(components, subcommand, parents)
                else:
                    command = subcommand
            else:
                parent_names = [ x.name for x in parents ]
                command_name = "{} {}".format(" ".join(parent_names), name) if parent_names else name

                if parents:
                    command_parent = parents[-1]
                    command_parent.print()
                    command_parent.print_help()

                raise CommandNotExistsError("Command '{}' not found".format(command_name), parent)

        if isinstance(command, RouterCommand):
            return command
        else:
            return type(command)(command.name, command.parent_instance)

    command_args = re.split('\s+', full_name) if isinstance(full_name, str) else list(full_name)
    command = find(
        copy.copy(command_args),
        settings.MANAGER.index.command_tree
    )
    if parent:
        command.exec_parent = parent

        if parent.parent_messages:
            command.parent_messages = parent.parent_messages
        else:
            command.parent_messages = parent.messages

    return command


class CommandGenerator(object):

    def __init__(self, key, name, **options):
        self.parser = PythonParser({
            'settings': settings
        })
        self.key = key
        self.name = name

        self.full_spec = settings.MANAGER.get_spec()

        try:
            self.spec = self.full_spec[key]
            for name_component in name.split('.'):
                self.spec = self.spec[name_component]
        except Exception as e:
            raise CommandNotExistsError("Command specification {} {} does not exist".format(key, name))

        self.spec = self.parse_values(self.spec)

        self.class_name = get_command_name(self.key, self.name, self.spec)
        self.dynamic_class_name = get_dynamic_class_name(self.class_name)

        if options.get('base_command', None):
            self.base_command = options['base_command']
        else:
            from systems.commands import action
            self.base_command = action.ActionCommand

        module_info = self.get_module(name)
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
            if self.key == 'plugin_mixins':
                self.parents = [ self.get_command(self.spec['base'], CommandMixin) ]
            else:
                self.parents = [ self.get_command(self.spec['base'], BaseCommand) ]

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

        for parent in self.parents:
            parent.generate(command, self) # Allow parents to initialize class

        return command


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


def BaseCommand(name):
    return _Command('command_base', name)

def Command(lookup_path):
    return _Command('command', lookup_path)


def CommandMixin(name):
    from systems.commands.mixins import base
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
    # BaseCommand method overrides

    def __str__(self):
        class_name = command.class_name
        if not getattr(command.module, command.class_name, None):
            class_name = command.dynamic_class_name
        return "{} <{}>".format(class_name, command.name)

    def get_priority(self):
        return command.spec['priority']

    def server_enabled(self):
        return command.spec['server_enabled']

    def remote_exec(self):
        return command.spec['remote_exec']

    def groups_allowed(self):
        if command.spec['groups_allowed'] is False:
            return False

        from settings.roles import Roles
        return [ Roles.admin ] + ensure_list(command.spec['groups_allowed'])

    if 'parameters' in command.spec:
        for name, info in command.spec['parameters'].items():
            command.method(_get_parse_method(name, info))
            command.method(_get_check_method(name, info))
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
                elif isinstance(options, (bool, int, float, str, list, tuple)):
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

    if command.key == 'command':
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

            if 'alt_names' in info and info['alt_names'] is not None:
                schema_info[name]['alt_names'] = ensure_list(info['alt_names'])

            if 'data' in info and info['data'] is not None:
                schema_info[name]['data'] = info['data']
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
    klass = mixin.create()

    def __init__(self, *args, **kwargs):
        super(klass, self).__init__(*args, **kwargs)

        for name, info in schema_info.items():
            if 'model' in info:
                priority = 50
                if 'priority' in mixin.spec['meta'][name]:
                    priority = mixin.spec['meta'][name]['priority']
                self.facade_index["{:02d}_{}".format(priority, name)] = self.facade(info['model'].facade)

    if 'meta' in mixin.spec:
        klass.__init__ = __init__

    return klass


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
                help_text = help_text,
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
                help_text = help_text,
                value_label = value_label,
                default = ensure_list(default_value) if default_value is not None else []
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

            if help_callback:
                help_callback = getattr(self, help_callback, None)

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

def _get_check_method(method_base_name, method_info):
    def method(self):
        if 'default_callback' in method_info:
            default_callback = getattr(self, method_info['default_callback'], None)
            if default_callback is None:
                raise CallbackNotExistsError("Command parameter default callback {} does not exist".format(default_callback))
            default_value = default_callback()
        else:
            default_value = method_info.get('default', None)

        if method_info['parser'] == 'variables':
            values = self.options.get(method_base_name)
            if not default_value:
                return len(values) > 0

            return set(ensure_list(default_value)) != set(values)

        if default_value is None:
            return self.options.get(method_base_name) is not None

        return self.options.get(method_base_name) != default_value

    method.__name__ = "check_{}".format(method_base_name)
    return method

def _get_accessor_method(method_base_name, method_info):
    def accessor(self):
        if 'default_callback' in method_info:
            default_callback = getattr(self, method_info['default_callback'], None)
            if default_callback is None:
                raise CallbackNotExistsError("Command parameter default callback {} does not exist".format(default_callback))
            default_value = default_callback()
        else:
            default_value = method_info.get('default', None)

        value = self.options.get(method_base_name, default_value)

        if value is not None and method_info['parser'] == 'variables':
            value = ensure_list(value)

        if 'postprocessor' in method_info:
            postprocessor = getattr(self, method_info['postprocessor'], None)
            if postprocessor is None:
                raise CallbackNotExistsError("Command parameter postprocessor {} does not exist".format(postprocessor))

            if value is not None:
                value = postprocessor(value)
        return value

    accessor.__name__ = method_base_name
    return property(accessor)


def _generate_resource_commands(command, name, spec):
    data_spec = settings.MANAGER.get_spec('data.{}'.format(spec['resource']))

    base_name = spec.get('base_name', name)
    roles_spec = data_spec.get('roles', {})
    meta_spec = data_spec.get('meta', {})
    options_spec = copy.deepcopy(spec.get('options', {}))

    if 'provider_name' in meta_spec:
        provider = meta_spec['provider_name'].split(':')
        options_spec['provider_name'] = provider[0]
        options_spec['provider_subtype'] = provider[1] if len(provider) > 1 else None

    if 'edit' in roles_spec:
        options_spec['edit_roles'] = roles_spec['edit']

    if 'view' in roles_spec:
        options_spec['view_roles'] = roles_spec['view']

    resource.ResourceCommandSet(command,
        BaseCommand(spec['base']), base_name, spec['resource'],
        **options_spec
    )


def display_command_info(klass, prefix = '', display_function = logger.info, properties = True, methods = True):
    display_function("{}{}".format(prefix, klass.__name__))
    for parent in klass.__bases__:
        display_command_info(parent, "{}  << ".format(prefix), display_function)

    if properties:
        display_function("{} properties:".format(prefix))
        for attribute in dir(klass):
            if not attribute.startswith('__') and not callable(getattr(klass, attribute)):
                display_function("{}  ->  {}".format(prefix, attribute))

    if methods:
        display_function("{} methods:".format(prefix))
        for attribute in dir(klass):
            if not attribute.startswith('__') and callable(getattr(klass, attribute)):
                display_function("{}  **  {}".format(prefix, attribute))
