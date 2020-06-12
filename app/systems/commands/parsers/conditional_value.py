from .base import ParserBase

import re


class ConditionalValueParser(ParserBase):

    conditional_pattern = r'^\?\s*\{([^\}]+)\}\s+([^\:]+)\|(.+)$'


    def parse(self, value):
        if not isinstance(value, str):
            return value

        conditional_match = re.search(self.conditional_pattern, value)
        if conditional_match:
            if eval(conditional_match.group(1).strip()):
                value = eval(conditional_match.group(2).strip())
            else:
                value = eval(conditional_match.group(3).strip())

        return value
