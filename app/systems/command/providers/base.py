from django.utils.module_loading import import_string

import json


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


class BaseCommandProvider(object):

    def __init__(self, name, command):
        self.name = name
        self.command = command
        self.errors = []
        self.config = {}
        self.schema = ParamSchema()
        self.provider_options = {}
        self.test = False
        self.create = False


    def context(self, type, test = False):
        self.test = test
        return self


    def provider_config(self, type = None):
        # Override in subclass
        pass

    def provider_schema(self, type = None):
        self.schema.clear()
        self.provider_config(type)
        return self.schema.export()


    def requirement(self, type, name, callback = None, callback_args = [], help = None, config_name = None):
        config_value = self.command.get_config(config_name)
        
        self.schema.require(type, name, help, config_name)

        if not self.config.get(name, None):
            if config_value is not None:
                self.config[name] = config_value
            elif self.create:
                self.errors.append("Field '{}' required when adding {} instances".format(name, self.name))

        if name in self.config and self.config[name] is not None:
            self.config[name] = self.parse_value(type, self.config[name])

        if self.create and callback and callable(callback):
            callback_args = [callback_args] if not isinstance(callback_args, (list, tuple)) else callback_args
            callback(name, self.config[name], self.errors, *callback_args)
    
    def option(self, type, name, default = None, callback = None, callback_args = [], help = None, config_name = None):
        config_value = self.command.get_config(config_name)
        process = True

        self.schema.option(type, name, default, help, config_name)

        if not self.config.get(name, None):
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


    def field_help(self, type = None):
        help = ["fields as key value pairs (by provider)", ' ']

        def render(messages = '', prefix = ''):
            if not isinstance(messages, (tuple, list)):
                messages = [messages]

            for message in messages:
                help.append("{}{}".format(prefix, message))

        for name, provider in self.provider_options.items():
            provider = self._get_provider(name)
            schema = provider.provider_schema(type)

            render(("provider_name: {} ({})".format(self.command.success_color(name), self.provider_options[name]), ' '))

            if schema['requirements']:
                render('requirements:', '  ')
                for require in schema['requirements']:
                    param_help = "{}".format(self.command.warning_color(require['name']))
                    
                    if require['config_name']:
                        param_help += " (@{})".format(self.command.success_color(require['config_name']))
                    
                    param_help += " - {}".format(require['help'])
                    render(param_help, '    ')
                render()

            if schema['options']:
                render('options:', '  ')
                for option in schema['options']:
                    param_help = ["{}".format(self.command.warning_color(option['name']))]
                    
                    if option['config_name']:
                        param_help[0] += " (@{} | {})".format(
                            self.command.success_color(option['config_name']),
                            self.command.success_color(str(option['default']))
                        )
                    else:
                        param_help[0] += " ({})".format(self.command.success_color(str(option['default'])))
                    
                    param_help.append("   - {}".format(option['help']))
                    render(param_help, '    ')
            render()

        return help


    def _get_provider(self, name):
        try:
            if name not in self.provider_options.keys():
                raise Exception("Not supported")
            
            return import_string(self.provider_options[name])(name, self.command)
        
        except Exception as e:
            self.command.error("{} provider {} error: {}".format(self.provider_type.title(), name, str(e)))
