from systems.plugins.index import BaseProvider

import string
import json
import re


class Provider(BaseProvider('parser', 'state')):

    variable_pattern = r'^\$\{?([a-zA-Z][\_\-a-zA-Z0-9]+)(?:\[([^\]]+)\])?\}?$'
    variable_value_pattern = r'(?<!\$)\$\>?\{?([a-zA-Z][\_\-a-zA-Z0-9]+(?:\[[^\]]+\])?)\}?'


    def __init__(self, type, name, command, config):
        super().__init__(type, name, command, config)
        self.variables = {}


    def initialize(self, reset = False):
        if reset or not self.variables:
            self.variables = {}
            for state in self.command.get_instances(self.command._state):
                self.variables[state.name] = state.value


    def parse(self, value, config):
        if not isinstance(value, str):
            return value

        if re.search(self.variable_pattern, value):
            value = self.parse_variable(value, config)
        else:
            for ref_match in re.finditer(self.variable_value_pattern, value):
                variable_value = self.parse_variable("${}".format(ref_match.group(1)), config)
                if isinstance(variable_value, (list, tuple)):
                    variable_value = ",".join(variable_value)
                elif isinstance(variable_value, dict):
                    variable_value = json.dumps(variable_value)

                if variable_value:
                    value = value.replace(ref_match.group(0), str(variable_value)).strip()
        return value

    def parse_variable(self, value, config):
        state_match = re.search(self.variable_pattern, value)
        if state_match:
            variables = {**self.variables, **config.get('state_overrides', {})}
            new_value = state_match.group(1)
            key = state_match.group(2)

            if new_value in variables:
                data = variables[new_value]

                if key:
                    key = self.command.options.interpolate(key, **config.export())

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
