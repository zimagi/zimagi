from systems.plugins.index import ProviderMixin


class ListCalculationMixin(ProviderMixin('list_calculation')):

    def valid_list(self, list_data):
        if not isinstance(list_data, (list, tuple)) or len(list_data) == 0:
            return False

        if (self.field_min_values is not None and len(list_data) < self.field_min_values):
            return False
        return True

    def prepare_list(self, list_data):
        if self.field_reverse:
            list_data = list(reversed(list_data))
        return list_data
