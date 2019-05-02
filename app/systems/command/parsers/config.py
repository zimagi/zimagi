from .base import ParserBase

import string
import json
import re


class ConfigTemplate(string.Template):
    delimiter = '@'
    idpattern = r'[a-z][\_\-a-z0-9]*'


class ConfigParser(ParserBase):

    variable_pattern = r'^(@[a-z][\_\-a-z0-9]+)(?:\[([^\]]+)\])?$'
    runtime_variables = {}


    def __init__(self, command):
        super().__init__(command)
        self.variables = None
        self.norm_variables = None


    def initialize(self, reset = False):
        if reset or self.variables is None:
            self.variables = {}
            for config in self.command.get_instances(self.command._config):
                self.variables[config.name] = config.value

            for key, value in self.runtime_variables.items():
                self.variables[key] = value

            self.norm_variables = self._normalize_variables(self.variables)

    def _normalize_variables(self, variables):
        normalized = {}
        for name, value in variables.items():
            basic = True
            if isinstance(value, (list, tuple)):
                for item in value:
                    if isinstance(item, (list, dict)):
                        basic = False
                        break
                if basic:
                    value = ",".join(value)
                else:
                    value = json.dumps(value)
            elif isinstance(value, dict):
                value = json.dumps(value)
            else:
                value = str(value)

            normalized[name] = value
        return normalized


    def parse(self, value):
        if not isinstance(value, str):
            return value

        config_match = re.search(self.variable_pattern, value)
        if config_match:
            value = config_match.group(1)[1:]
            key = config_match.group(2)

            if value in self.variables:
                data = self.variables[value]
                if isinstance(data, dict) and key:
                    return data[key]
                elif isinstance(data, (list, tuple)) and key:
                    return data[int(key)]
                else:
                    return data

            self.command.error("Configuration {} does not exist, escape literal with @@".format(value))

        parser = ConfigTemplate(value)
        try:
            return parser.substitute(**self.norm_variables)

        except KeyError as e:
            self.command.error("Configuration {} does not exist, escape literal with @@".format(e))
