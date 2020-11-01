from systems.plugins.index import BasePlugin


class BaseProvider(BasePlugin('formatter')):

    def __init__(self, type, name, command, config):
        super().__init__(type, name, command)
        self.config = config


    def format(self, value, record):
        # Override in subclass.
        return value

    def format_value(self, value, record, provider, **config):
        if 'id' not in config:
            config['id'] = self.field_id

        return self.command.get_provider(
            'formatter',
            provider,
            config
        ).format(value, record)


    def error(self, message):
        self.command.error("Formatter {} {} failed: {}".format(self.name, self.field_id, message))
