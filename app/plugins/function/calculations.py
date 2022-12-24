from systems.plugins.index import BaseProvider

import re


class Provider(BaseProvider('function', 'calculations')):

    def exec(self, pattern):
        calculation_names = []
        for name in self.manager.get_spec('calculation').keys():
            if re.match(r'{}'.format(pattern), name):
                calculation_names.append(name)
        return calculation_names
