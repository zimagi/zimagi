from systems.plugins.index import BaseProvider

import re


class Provider(BaseProvider('parser', 'conditional_value')):

    conditional_pattern = r'^\?\>([^\?]+)\?([^\|]+)\|(.+)$'


    def parse(self, value, config):
        if not isinstance(value, str):
            return value

        conditional_match = re.search(self.conditional_pattern, value)
        if conditional_match:
            if eval(conditional_match.group(1).strip()):
                value = eval(conditional_match.group(2).strip())
            else:
                value = eval(conditional_match.group(3).strip())

        return value
