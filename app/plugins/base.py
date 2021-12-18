from pydoc import locate
from django.conf import settings

import copy
import json


class GeneratorError(Exception):
    pass


class ParamSchema(object):

    def __init__(self):
        self.clear()

    def clear(self):
        self.schema = {
            'requirements': [],
            'options': []
        }

    def require(self, type, name, help, config_name):
        if name in self.schema['options']:
            return
        if name not in self.schema['requirements']:
            self.schema['requirements'].append({
                'type': type,
                'name': name,
                'help': help,
                'config_name': config_name
            })

    def option(self, type, name, default, help, config_name):
        self.schema['options'].append({
            'type': type,
            'name': name,
            'default': default,
            'help': help,
            'config_name': config_name
        })

    def export(self):
        return self.schema


class BasePlugin(object):

    @classmethod
    def generate(cls, plugin, generator):

        def get_config(name, default):
            def config_accessor(self):
                return self.config.get(name, default)
            return property(config_accessor)

        for config_type in ('requirement', 'option'):
            for name, info in plugin.meta.get(config_type, {}).items():
                setattr(plugin, "field_{}".format(name), get_config(name, info.get('default', None)))

        def check_system(cls):
            return generator.spec['system']

        if 'system' in generator.spec:
            plugin.check_system = classmethod(check_system)


    def __init__(self, type, name, command):
        self.name = name
        self.command = command
        self.errors = []
        self.config = {}
        self.schema = ParamSchema()
        self.provider_type = type
        self.provider_options = self.manager.index.get_plugin_providers(self.provider_type)

        self.test = False
        self.create_op = False


    @property
    def manager(self):
        return settings.MANAGER


    def context(self, subtype, test = False):
        self.test = test
        return self

    @classmethod
    def check_system(cls):
        # Override in subclass
        return False


    def import_config(self, config):
        self.provider_schema()
        schema = self.schema.export()

        for requirement in schema['requirements']:
            name = requirement['name']

            if name not in config:
                self.command.error("Configuration {} required for plugin provider {} {}".format(name, self.provider_type, self.name))

            self.config[name] = config[name] if isinstance(config[name], requirement['type']) else requirement['type'](config[name])

        for option in schema['options']:
            name = option['name']

            if name not in config:
                config[name] = copy.deepcopy(option['default'])
            else:
                self.config[name] = config[name] if isinstance(config[name], option['type']) else option['type'](config[name])


    def provider_config(self, type = None):
        for name, info in self.meta.get('requirement', {}).items():
            info = copy.deepcopy(info)
            self.requirement(locate(info.pop('type')), name, **info)

        for name, info in self.meta.get('option', {}).items():
            info = copy.deepcopy(info)
            self.option(locate(info.pop('type')), name, **info)


    def provider_schema(self, type = None):
        self.schema.clear()
        self.provider_config(type)
        return self.schema.export()


    def get_fields(self, type = None):
        schema = self.provider_schema(type)
        fields = []
        for field_type, field_data in schema.items():
            for field_info in field_data:
                fields.append(field_info['name'])
        return fields


    def requirement(self, type, name, callback = None, callback_args = None, help = None, config_name = None):
        if not callback_args:
            callback_args = []

        config_value = self.command.get_config(config_name)

        self.schema.require(type, name, help, config_name)

        if self.config.get(name, None) is None:
            if config_value is not None:
                self.config[name] = config_value
            elif self.create_op:
                self.errors.append("Field '{}' required when adding {} instances".format(name, self.name))

        if name in self.config and self.config[name] is not None:
            self.config[name] = self.parse_value(type, self.config[name])

        if self.create_op and callback and callable(callback):
            callback_args = [callback_args] if not isinstance(callback_args, (list, tuple)) else callback_args
            callback(name, self.config[name], self.errors, *callback_args)

    def option(self, type, name, default = None, callback = None, callback_args = None, help = None, config_name = None):
        if not callback_args:
            callback_args = []

        config_value = self.command.get_config(config_name)
        process = True

        self.schema.option(type, name, default, help, config_name)

        if self.config.get(name, None) is None:
            if config_value is not None:
                self.config[name] = config_value
            else:
                self.config[name] = default
                process = False

        if self.config[name] is not None:
            self.config[name] = self.parse_value(type, self.config[name])

        if process and callback and callable(callback):
            callback_args = [callback_args] if not isinstance(callback_args, (list, tuple)) else callback_args
            callback(name, self.config[name], self.errors, *callback_args)

    def parse_value(self, type, value):
        if isinstance(value, type):
            return value

        if type == int:
            return int(value)
        if type == float:
            return float(value)
        if type == str:
            return str(value)
        if type == bool:
            return json.loads(value.lower())
        if type == list:
            return [ x.strip() for x in value.split(',') ]
        if type == dict:
            return json.loads(value)

    def validate(self):
        if self.errors:
            self.command.error("\n".join(self.errors))


    def field_help(self, type = None, exclude_fields = None):
        help = [' ']

        def render(messages = '', prefix = ''):
            if not isinstance(messages, (tuple, list)):
                messages = [messages]

            for message in messages:
                help.append("{}{}".format(prefix, message))

        for name, provider_class in self.provider_options.items():
            provider = provider_class(self.provider_type, name, self.command)
            schema = provider.provider_schema(type)

            render("-" * 40)
            render(("provider: {}".format(self.command.relation_color(name)), ' '))

            if schema['requirements']:
                render('provider requirements:', '  ')
                for require in schema['requirements']:
                    if exclude_fields and require['name'] in exclude_fields:
                        continue

                    param_help = "{}".format(self.command.warning_color(require['name']))

                    if require['config_name']:
                        param_help += " (@{})".format(self.command.key_color(require['config_name']))

                    param_help += " - {}".format(require['help'])
                    render(param_help, '    ')
                render()

            if schema['options']:
                render('provider options:', '  ')
                for option in schema['options']:
                    if exclude_fields and option['name'] in exclude_fields:
                        continue

                    param_help = ["{}".format(self.command.warning_color(option['name']))]

                    if option['config_name']:
                        default = self.command.get_config(option['config_name'])
                        if default is None:
                            config_label = self.command.key_color(option['config_name'])
                            default = option['default']
                        else:
                            config_label = self.command.success_color(option['config_name'])

                        if default is not None:
                            param_help[0] += " (@{} | {})".format(
                                config_label,
                                self.command.value_color(default)
                            )
                        else:
                            param_help[0] += " (@{})".format(config_label)

                    elif option['default'] is not None:
                        param_help[0] += " ({})".format(self.command.value_color(option['default']))

                    param_help.append("   - {}".format(option['help']))
                    render(param_help, '    ')
            render()

        return help


    def run_list(self, items, callback):
        return self.command.run_list(items, callback)

    def run_exclusive(self, lock_id, callback, error_on_locked = False, timeout = 600, interval = 2):
        return self.command.run_exclusive(lock_id, callback,
            error_on_locked = error_on_locked,
            timeout = timeout,
            interval = interval
        )
