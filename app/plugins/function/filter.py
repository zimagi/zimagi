from systems.plugins.index import BaseProvider


class Provider(BaseProvider('function', 'filter')):

    def exec(self, data, **filters):
        filtered_data = {}

        for key, value in data.items():
            add_key = True

            for filter_param, filter_value in filters.items():
                if filter_param in value:
                    if value[filter_param] != filter_value:
                        add_key = False
                elif not isinstance(filter_value, bool) or filter_value == True:
                    add_key = False

            if add_key:
                filtered_data[key] = value

        return filtered_data
