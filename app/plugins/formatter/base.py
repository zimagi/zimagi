from systems.plugins.index import BasePlugin


class BaseProvider(BasePlugin('formatter')):

    def __init__(self, type, name, command, config):
        super().__init__(type, name, command)
        self.config = config


    def format(self, value):
        # Override in subclass.
        return value


    def error(self, message):
        self.command.error("Formatter {} {} failed: {}".format(name, self.field_id, message))
