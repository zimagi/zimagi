from systems.plugins.index import BaseProvider


class Provider(BaseProvider("field_processor", "bool_to_number")):
    def exec(self, dataset, field_data):
        return field_data.map({True: 1, False: 0})
