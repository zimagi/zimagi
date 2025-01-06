import copy
from collections import OrderedDict
from functools import lru_cache

from django.conf import settings
from utility.data import sorted_keys


class AppOptions:
    def __init__(self, command):
        self.command = command
        self.config = {}
        self._options = {}

        self.parser_spec = settings.MANAGER.get_spec("plugin.parser.providers")
        self.parsers = OrderedDict()

        providers = self.command.manager.index.get_plugin_providers("parser", True)

        for name in sorted_keys(self.parser_spec, "weight"):
            spec = self.parser_spec[name]
            if spec.get("interpolate", True):
                self.parsers[name] = providers[name]("parser", name, self.command, spec)

    def __getitem__(self, name):
        return self.get(name, None)

    def __setitem__(self, name, value):
        self._options[name] = value

    def get_parser(self, name):
        if name in self.parsers:
            return self.parsers[name]
        return None

    @lru_cache(maxsize=None)
    def load_config(self):
        if getattr(settings, "DB_LOCK", None):
            for config in self.command._config.filter(name__startswith="option_"):
                self.config[config.name] = config.value

    def get_default(self, name, default=None):
        self.load_config()

        config_name = f"option_{name}"
        if config_name in self.config:
            return self.config[config_name]
        return default

    def initialize(self, reset=False):
        for name, parser in self.parsers.items():
            parser.initialize(reset)

    def interpolate(self, value, config=None, config_value=True, config_default=False, **options):
        for name, parser in self.parsers.items():
            if not config or parser.config.get(config, config_default) == config_value:
                value = parser.interpolate(value, options)
        return value

    def check(self, name):
        return name in self._options

    def get(self, name):
        if self.check(name):
            return self._options[name]
        return self.get_default(name, None)

    def add(self, name, value, interpolate=True):
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
