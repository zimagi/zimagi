import re

from systems.plugins.index import BaseProvider


class Provider(BaseProvider("function", "split")):
    def exec(self, str_value, split_value=","):
        return re.split(split_value, str_value)
