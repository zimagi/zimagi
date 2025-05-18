from systems.plugins.index import BaseProvider


class Provider(BaseProvider("function", "flatten")):
    def exec(self, *elements):
        values = []

        def flatten(value):
            if isinstance(value, (list, tuple)):
                for item in value:
                    flatten(item)
            else:
                values.append(value)

        for element in elements:
            flatten(element)

        return values
