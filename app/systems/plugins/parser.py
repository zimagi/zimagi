from utility.data import normalize_value

import re


class FormatterParserError(Exception):
    pass


class FormatterParser(object):

    formatter_pattern = r'^\#([a-zA-Z][\_\-a-zA-Z0-9]+)\(([^\,]+)\s*\,(.*?)\)'


    def __init__(self, id, command):
        self.id = id
        self.command = command


    def parse(self, id, value, record):
        if not isinstance(value, str) or '#' not in value:
            return value

        formatter_match = re.search(self.function_pattern, value)

        if formatter_match:
            provider = formatter_match.group(1)
            config = { 'id': "{}:{}".format(self.id, id) }

            initial_value = formatter_match.group(2)
            if initial_value in record:
                initial_value = record[initial_value]

            if formatter_match.group(3):
                for parameter in re.split(r'\s*\,\s*', formatter_match.group(3)):
                    parameter = parameter.strip()
                    option_components = parameter.split('=')

                    if len(option_components) == 2:
                        option_name = option_components[0].strip()
                        value = option_components[1].strip()
                        config[option_name] = normalize_value(value, strip_quotes = True, parse_json = True)
                    else:
                        raise FormatterParserError("All options passed to formatter parser must be key value pairs ({} given)".format(value))

            return self.command.get_provider(
                'formatter', provider, config
            ).format(initial_value, record)
        return value
