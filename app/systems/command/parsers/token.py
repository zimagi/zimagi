from .base import ParserBase
from utility.data import create_token

import re


class TokenParser(ParserBase):

    token_pattern = r'^\%([\%\-])([a-zA-Z][\_\-a-zA-Z0-9]+)(?:\:(\d+))?$'


    def parse(self, value):
        if not isinstance(value, str):
            return value

        ref_match = re.search(self.token_pattern, value)
        if ref_match:
            operation = ref_match.group(1)
            length = ref_match.group(3)
            if length:
                length = int(length)
            else:
                length = 20

            state_name = "token-{}-{}".format(ref_match.group(2), length)

            if operation == '%':
                value = self.command.get_state(state_name)
            else:
                value = None

            if not value:
                value = create_token(length)
                self.command.set_state(state_name, value)

        return value
