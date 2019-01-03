from .base import OpMixin


class ListMixin(OpMixin):
    
    def exec_list(self, facade, *fields, **filters):
        if facade.count():
            self.table(facade.render_values(*fields, **filters), '{}_list'.format(facade.name))


    def _exec_processed_list(self, facade, process_func, *fields, **filters):
        data = []

        if facade.count():
            data = facade.render(fields, facade.values(*fields, **filters))
            key_index = data[0].index(facade.key())

            for index, info in enumerate(data):
                if index == 0:
                    process_func('label', info, key_index)
                else:
                    process_func('data', info, key_index)
        
        return data

    def exec_processed_list(self, facade, process_func, *fields, **filters):
        data = self._exec_processed_list(facade, process_func, *fields, **filters)
        if len(data):
            self.table(data, '{}_list'.format(facade.name))

    def exec_processed_sectioned_list(self, facade, process_func, *fields, **filters):
        data = self._exec_processed_list(facade, process_func, *fields, **filters)
        if len(data):
            for index in range(1, len(data)):
                section_data = [data[0]]
                section_data.append(data[index])
                self.table(section_data, '{}_list'.format(facade.name))


    def exec_list_related(self, facade, key, relation, relation_facade, *fields, **filters):
        queryset = facade.related(key, relation, **filters)
        
        if queryset:
            self.table(relation_facade.render(fields, queryset.values(*fields)), '{}_{}_list'.format(facade.name, relation))
