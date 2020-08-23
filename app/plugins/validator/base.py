from systems.plugins.index import BasePlugin


class BaseProvider(BasePlugin('validator')):

    def __init__(self, type, name, command, config):
        super().__init__(type, name, command)
        self.config = config


    def validate(self, value):
        # Override in subclass.
        return True


    def warning(self, message):
        self.command.warning("Validator {} {} failed: {}".format(name, self.field_id, message))