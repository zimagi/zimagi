from systems.plugins.index import BaseProvider
from utility.data import dump_json

import re


class Provider(BaseProvider('parser', 'state')):

    variable_pattern = r'^\$\{?([a-zA-Z\<][\_\-a-zA-Z0-9\.\<\>]*)(?:\[([^\]]+)\])?\}?$'
    variable_value_pattern = r'(?<!\$)\$\>?\{?([a-zA-Z\<][\_\-a-zA-Z0-9\.\<\>]*(?:\[[^\]]+\])?)\}?'


    @classmethod
    def _load_state_variables(cls, command, reset = False):
        if reset or not getattr(cls, '_state_variables', None):
            cls._state_variables = {}
            for state in command._state.all():
                cls._state_variables[state.name] = state.value
        return cls._state_variables


    def __init__(self, type, name, command, config):
        super().__init__(type, name, command, config)
        self.variables = {}


    def initialize(self, reset = False):
        if reset or not self.variables:
            self.variables = self._load_state_variables(self.command, reset)


    def parse(self, value, config):
        if not isinstance(value, str) or '$' not in value:
            return value

        if re.search(self.variable_pattern, value):
            value = self.parse_variable(value, config)
        else:
            for ref_match in re.finditer(self.variable_value_pattern, value):
                variable = "${}".format(ref_match.group(1))
                variable_value = self.parse_variable(variable, config)

                if isinstance(variable_value, str) and variable_value and variable_value[0] == '$':
                    full_variable = '${' + variable_value[1:] + '}'
                    if variable_value == variable and full_variable in value:
                        variable_value = full_variable

                elif isinstance(variable_value, (list, tuple)):
                    variable_value = ",".join(variable_value)

                elif isinstance(variable_value, dict):
                    variable_value = dump_json(variable_value)

                if variable_value is not None:
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
