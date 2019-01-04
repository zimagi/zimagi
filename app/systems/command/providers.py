from django.utils.module_loading import import_string


class ParamSchema(object):

    def __init__(self):
        self.clear()

    def clear(self):
        self.schema = {
            'requirements': [],
            'options': []
        }

    def require(self, name, help):
        if name in self.schema['options']:
            return
        if name not in self.schema['requirements']:
            self.schema['requirements'].append({
                'name': name,
                'help': help
            })

    def option(self, name, default, help):
        self.schema['options'].append({
            'name': name,
            'default': default,
            'help': help
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


    def provider_config(self):
        # Override in subclass
        pass

    def provider_schema(self):
        self.schema.clear()
        self.provider_config()
        return self.schema.export()


    def validate(self):
        if self.errors:
            self.command.error("\n".join(self.errors))
    
    def option(self, name, default = None, callback = None, help = None):
        self.schema.option(name, default, help)

        if not self.config.get(name, None):
            self.config[name] = default
        
        elif callback and callable(callback):
            callback(name, self.config[name], self.errors)        

    def requirement(self, name, callback = None, help = None):
        self.schema.require(name, help)

        if not self.config.get(name, None):
            self.errors.append("Field '{}' required when adding {} instances".format(name, self.name))
        
        elif callback and callable(callback):
            callback(name, self.config[name], self.errors)


    def field_help(self):
        help = ["fields as key value pairs (by provider)", ' ']

        def render(messages = '', prefix = ''):
            if not isinstance(messages, (tuple, list)):
                messages = [messages]

            for message in messages:
                help.append("{}{}".format(prefix, message))

        for name, provider in self.provider_options.items():
            provider = self._get_provider(name)
            schema = provider.provider_schema()

            render(("provider_name: {} ({})".format(self.command.success_color(name), self.provider_options[name]), ' '))

            if schema['requirements']:
                render('requirements:', '  ')
                for require in schema['requirements']:
                    render("{} - {}".format(self.command.warning_color(require['name']), require['help']), '    ')
                render()

            if schema['options']:
                render('options:', '  ')
                for option in schema['options']:
                    render("{} ({}) - {}".format(self.command.warning_color(option['name']), self.command.success_color(str(option['default'])), option['help']), '    ')

            render()

        return help


    def _get_provider(self, name):
        try:
            if name not in self.provider_options.keys():
                raise Exception("Not supported")
            
            return import_string(self.provider_options[name])(name, self.command)
        
        except Exception as e:
            self.command.error("{} provider {} error: {}".format(self.provider_type.title(), name, str(e)))
