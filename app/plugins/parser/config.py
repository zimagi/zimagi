from django.conf import settings

from systems.plugins.index import BaseProvider
from utility.data import Collection, dump_json

import re


class Provider(BaseProvider('parser', 'config')):

    variable_pattern = r'^\@\{?([a-zA-Z][\_\-a-zA-Z0-9]*)(?:\[([^\s]+)\])?\}?$'
    variable_value_pattern = r'(?<!\@)\@(\>\>?)?\{?([a-zA-Z][\_\-a-zA-Z0-9]*(?:\[[^\s]+\])?)\}?'


    @classmethod
    def _load_settings(cls, reset = False):
        if reset or not getattr(cls, '_settings_variables', None):
            cls._settings_variables = {}
            for setting in dir(settings):
                if setting == setting.upper():
                    config_value = getattr(settings, setting)

                    if isinstance(config_value, (bool, int, float, str, list, tuple, dict)):
                        cls._settings_variables[setting] = config_value
        return cls._settings_variables

    @classmethod
    def _load_config_variables(cls, command, reset = False):
        if reset or not getattr(cls, '_config_variables', None):
            cls._config_variables = {}
            for config in command._config.all():
                cls._config_variables[config.name] = config.value
        return cls._config_variables


    def __init__(self, type, name, command, config):
        super().__init__(type, name, command, config)
        self.variables = {}


    def initialize(self, reset = False):
        if reset or not self.variables:
            self.variables = {
                **self._load_settings(reset),
                **self._load_config_variables(self.command, reset)
            }


    def check(self, name):
        return True if name in self.variables else False

    def set(self, name, value):
        self.variables[name] = value

    def get(self, name, default = None):
        return self.variables.get(name, default)


    def parse(self, value, config):
        if not isinstance(value, str) or '@' not in value:
            return value

        if re.search(self.variable_pattern, value):
            value = self.parse_variable(value, config)
        else:
            for ref_match in re.finditer(self.variable_value_pattern, value):
                formatter = ref_match.group(1)
                variable_value = self.parse_variable("@{}".format(ref_match.group(2)), config)
                if (formatter and formatter == '>>') or isinstance(variable_value, dict):
                    variable_value = dump_json(variable_value)
                elif isinstance(variable_value, (list, tuple)):
                    variable_value = ",".join(variable_value)

                if variable_value is not None:
                    value = value.replace(ref_match.group(0), str(variable_value)).strip()
        return value

    def parse_variable(self, value, config):
        config_match = re.search(self.variable_pattern, value)
        if config_match:
            variables = {**self.variables, **config.get('config_overrides', {})}
            new_value = config_match.group(1)
            keys = config_match.group(2)

            if new_value in variables:
                data = variables[new_value]

                if keys:
                    for key in keys.split(']['):
                        if isinstance(key, str):
                            key = self.command.options.interpolate(key, **config.export())

                        if isinstance(data, dict):
                            try:
                                data = data[key]
                            except KeyError:
                                return value

                        elif isinstance(data, (list, tuple)):
                            try:
                                data = data[int(key)]
                            except KeyError:
                                return value
                return data

        # Not found, assume desired
        return value
