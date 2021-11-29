from systems.plugins.index import BasePlugin


class BaseProvider(BasePlugin('validator')):

    def __init__(self, type, name, command, config):
        super().__init__(type, name, command)
        self.config = config


    def validate(self, value, record):
        # Override in subclass.
        return True


    def warning(self, message):
        self.command.warning("Validator {} {} failed: {}".format(self.name, self.field_id, message))
