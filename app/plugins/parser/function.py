from systems.plugins.index import BaseProvider
from utility.data import normalize_value, dump_json

import re


class Provider(BaseProvider('parser', 'function')):

    function_pattern = r'^\#(?:\[([^\]]+)\])?([a-zA-Z][\_\-a-zA-Z0-9]+)\((.*?)\)'
    function_value_pattern = r'(?<!\#)\#\>?((?:\[[^\]]+\])?[a-zA-Z][\_\-a-zA-Z0-9]+\(.*?\))'


    def parse(self, value, config):
        if not isinstance(value, str):
            return value

        standalone_function = re.search(self.function_pattern, value)
        if standalone_function and len(standalone_function.group(0)) == len(value):
            value = self.exec_function(value, config)
        else:
            for ref_match in re.finditer(self.function_value_pattern, value):
                function_value = self.exec_function("#{}".format(ref_match.group(1)), config)
                if isinstance(function_value, (list, tuple)):
                    function_value = ",".join(function_value)
                elif isinstance(function_value, dict):
                    function_value = dump_json(function_value)

                if function_value:
                    value = value.replace(ref_match.group(0), str(function_value)).strip()
        return value

    def exec_function(self, value, config):
        function_match = re.search(self.function_pattern, value)
        exec_function = True

        if config.function_suppress:
            config.function_suppress = re.compile(config.function_suppress)

        if function_match:
            function_variable = function_match.group(1)
            function_name = function_match.group(2)
            function_parameters = []

            if function_match.group(3):
                function_parameters = []
                function_options = {}

                for parameter in re.split(r'\s*\,\s*', function_match.group(3)):
                    parameter = parameter.strip()
                    option_components = parameter.split('=')

                    if len(option_components) == 2:
                        option_name = option_components[0].strip()
                        value = option_components[1].strip().lstrip("\'\"").rstrip("\'\"")

                        if config.function_suppress and config.function_suppress.match(value):
                            exec_function = False
                        else:
                            value = self.command.options.interpolate(value, **config.export())

                        function_options[option_name] = normalize_value(value, strip_quotes = False, parse_json = True)
                    else:
                        parameter = parameter.lstrip("\'\"").rstrip("\'\"")

                        if config.function_suppress and config.function_suppress.match(parameter):
                            exec_function = False
                        else:
                            parameter = self.command.options.interpolate(parameter, **config.export())

                        function_parameters.append(normalize_value(parameter, strip_quotes = False, parse_json = True))

            if exec_function:
                function = self.command.get_provider('function', function_name)
                result = function.exec(*function_parameters, **function_options)

                if function_variable:
                    self.command.options.get_parser('config').set(function_variable, result)
                return result
            else:
                if function_options:
                    parameter_str = ''
                    if function_parameters:
                        parameter_str = "{}, ".format(", ".join(function_parameters))

                    option_str = []
                    for name, value in function_options.items():
                        option_str.append("{} = {}".format(name, value))
                    option_str = ", ".join(option_str)

                    return "#{}({}{})".format(function_name, parameter_str, option_str)
                return "#{}({})".format(function_name, ", ".join(function_parameters))

        # Not found, assume desired
        return value
