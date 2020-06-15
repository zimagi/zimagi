from collections import OrderedDict

from django.conf import settings

from systems.commands.parsers import state, config, reference, token, conditional_value
from utility.data import ensure_list

import copy


class AppOptions(object):

    def __init__(self, command):
        self.command = command
        self._options = {}

        self.parsers = OrderedDict()
        self.parsers['token'] = token.TokenParser(command)
        self.parsers['state'] = state.StateParser(command)
        self.parsers['config'] = config.ConfigParser(command)
        self.parsers['reference'] = reference.ReferenceParser(command)
        self.parsers['conditional_value'] = conditional_value.ConditionalValueParser(command)

    def initialize(self, reset = False):
        for name, parser in self.parsers.items():
            parser.initialize(reset)

    def interpolate(self, value, parsers = None):
        if not parsers:
            parsers = []

        parsers = ensure_list(parsers)
        for name, parser in self.parsers.items():
            if not parsers or name in parsers:
                value = parser.interpolate(value)
        return value


    def get(self, name, default = None):
        return self._options.get(name, default)

    def add(self, name, value, interpolate = True):
        if interpolate:
            env = self.command.get_env()

        if interpolate and self.command.interpolate_options():
            self.initialize()
            self._options[name] = self.interpolate(value)
        else:
            self._options[name] = value

        return self._options[name]

    def remove(self, name):
        return self._options.pop(name)

    def clear(self):
        self._options.clear()

    def export(self):
        return copy.deepcopy(self._options)
