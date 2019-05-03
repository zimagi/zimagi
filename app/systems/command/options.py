from django.conf import settings

from systems.command.parsers import config, reference


class AppOptions(object):

    def __init__(self, command):
        self.command = command
        self._options = {}
        self.parsers = [
            config.ConfigParser(command),
            reference.ReferenceParser(command)
        ]

    def initialize(self, reset = False):
        for parser in self.parsers:
            parser.initialize(reset)

    def interpolate(self, value):
        for parser in self.parsers:
            value = parser.interpolate(value)
        return value


    def get(self, name, default = None):
        return self._options.get(name, default)

    def add(self, name, value):
        env = self.command.get_env()

        if self.command.interpolate_options() and (not env.host or (self.command.remote_exec() and settings.API_EXEC)):
            self.initialize()
            self._options[name] = self.interpolate(value)
        else:
            self._options[name] = value

        return self._options[name]

    def rm(self, name):
        return self._options.pop(name)

    def clear(self):
        self._options.clear()

    def export(self):
        return self._options
