from .base import ParserBase

import string
import json
import re


class ConfigTemplate(string.Template):
    delimiter = '@'
    idpattern = r'[a-z][\_\-a-z0-9]*'


class ConfigParser(ParserBase):

    variable_pattern = r'^(?<!\@)\@\{?([a-zA-Z][\_\-a-zA-Z0-9]+)(?:\[([^\]]+)\])?\}?$'
    variable_value_pattern = r'(?<!\@)\@\{?([a-zA-Z][\_\-a-zA-Z0-9]+(?:\[[^\]]+\])?)\}?'
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

        if re.search(self.variable_pattern, value):
            value = self.parse_variable(value)
        else:
            for ref_match in re.finditer(self.variable_value_pattern, value):
                variable_value = self.parse_variable("@{}".format(ref_match.group(1)))
                if isinstance(variable_value, (list, tuple)):
                    variable_value = ",".join(variable_value)
                elif isinstance(variable_value, dict):
                    variable_value = json.dumps(variable_value)

                if variable_value:
                    value = value.replace(ref_match.group(0), variable_value)
        return value

    def parse_variable(self, value):
        config_match = re.search(self.variable_pattern, value)
        if config_match:
            value = config_match.group(1)
            key = config_match.group(2)

            if value in self.variables:
                data = self.variables[value]
                if isinstance(data, dict) and key:
                    return data[key]
                elif isinstance(data, (list, tuple)) and key:
                    return data[int(key)]
                else:
                    return data

        # Not found, assume desired
        return '@' + value
