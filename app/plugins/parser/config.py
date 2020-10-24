from systems.plugins.index import BaseProvider

import string
import json
import re


class ConfigTemplate(string.Template):
    delimiter = '@'
    idpattern = r'[a-zA-Z][\_\-a-zA-Z0-9]+'


class Provider(BaseProvider('parser', 'config')):

    variable_pattern = r'^\@\{?([a-zA-Z][\_\-a-zA-Z0-9]+)(?:\[([^\]]+)\])?\}?$'
    variable_value_pattern = r'(?<!\@)\@(\>\>?)?\{?([a-zA-Z][\_\-a-zA-Z0-9]+(?:\[[^\]]+\])?)\}?'
    runtime_variables = {}


    def __init__(self, type, name, command, config):
        super().__init__(type, name, command, config)
        self.variables = {}


    def initialize(self, reset = False):
        if reset or not self.variables:
            self.variables = {}
            for config in self.command.get_instances(self.command._config):
                self.variables[config.name] = config.value


    def parse(self, value):
        if not isinstance(value, str):
            return value

        if re.search(self.variable_pattern, value):
            value = self.parse_variable(value)
        else:
            for ref_match in re.finditer(self.variable_value_pattern, value):
                formatter = ref_match.group(1)
                variable_value = self.parse_variable("@{}".format(ref_match.group(2)))
                if (formatter and formatter == '>>') or isinstance(variable_value, dict):
                    variable_value = json.dumps(variable_value)
                elif isinstance(variable_value, (list, tuple)):
                    variable_value = ",".join(variable_value)

                if variable_value is not None:
                    value = value.replace(ref_match.group(0), str(variable_value)).strip()
        return value

    def parse_variable(self, value):
        config_match = re.search(self.variable_pattern, value)
        if config_match:
            variables = {**self.runtime_variables, **self.variables}
            new_value = config_match.group(1)
            key = config_match.group(2)

            if new_value in variables:
                data = variables[new_value]
                if isinstance(data, dict) and key:
                    try:
                        return data[key]
                    except KeyError:
                        return value
                elif isinstance(data, (list, tuple)) and key:
                    try:
                        return data[int(key)]
                    except KeyError:
                        return value
                else:
                    return data

        # Not found, assume desired
        return value
