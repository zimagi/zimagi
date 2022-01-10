from systems.plugins.index import BaseProvider
from utility.data import normalize_value

import re


class Provider(BaseProvider('parser', 'conditional_value')):

    conditional_pattern = r'^\?\>([^\?]+)\?([^\|]+)\|(.+)$'


    def parse(self, value, config):
        if not isinstance(value, str):
            return value

        conditional_match = re.search(self.conditional_pattern, value)
        if conditional_match:
            try:
                test_element = normalize_value(self.command.options.interpolate(conditional_match.group(1).strip(), **config.export()))
                test = eval(test_element) if isinstance(test_element, str) else test_element
            except NameError:
                test = test_element

            if test:
                try:
                    true_value = normalize_value(self.command.options.interpolate(conditional_match.group(2).strip(), **config.export()))
                    value = eval(true_value) if isinstance(true_value, str) else true_value
                except NameError:
                    value = true_value
            else:
                try:
                    false_value = normalize_value(self.command.options.interpolate(conditional_match.group(3).strip(), **config.export()))
                    value = eval(false_value) if isinstance(false_value, str) else false_value
                except NameError:
                    value = false_value

        return value
