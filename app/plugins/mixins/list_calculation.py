from systems.plugins.index import ProviderMixin


class ListCalculationMixin(ProviderMixin('list_calculation')):

    def prepare_list(self, list_data):
        if not isinstance(list_data, (list, tuple)):
            self.abort("Calculation requires a list parameter")

        list_data = [value for value in list(list_data) if value is not None]

        if len(list_data) == 0 or (self.field_min_values is not None and len(list_data) < self.field_min_values):
            self.set_null()

        return reversed(list_data) if self.field_reverse else list_data
