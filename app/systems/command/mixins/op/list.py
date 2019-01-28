from .base import OpMixin


class ListMixin(OpMixin):
    
    def exec_list(self, facade, *fields, **filters):
        if facade.count():
            field_names, field_labels = self._get_field_info(fields)
            
            data = facade.render_values(*field_names, **filters)
            data[0] = field_labels
            
            self.table(data, '{}_list'.format(facade.name))


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
        field_names, field_labels = self._get_field_info(fields)

        data = self._exec_processed_list(facade, process_func, *field_names, **filters)
        if len(data):
            data[0] = field_labels + data[0][len(field_labels):]
            self.table(data, '{}_list'.format(facade.name))

    def exec_processed_sectioned_list(self, facade, process_func, *fields, **filters):
        field_names, field_labels = self._get_field_info(fields)

        data = self._exec_processed_list(facade, process_func, *field_names, **filters)
        if len(data):
            data[0] = field_labels + data[0][len(field_labels):]
            for index in range(1, len(data)):
                section_data = [data[0]]
                section_data.append(data[index])
                self.table(section_data, '{}_list'.format(facade.name))


    def exec_list_related(self, facade, key, relation, relation_facade, *fields, **filters):
        field_names, field_labels = self._get_field_info(fields)
        queryset = facade.related(key, relation, **filters)
        
        if queryset:
            data = relation_facade.render(fields, queryset.values(*field_names))
            data[0] = field_labels
            self.table(data, '{}_{}_list'.format(facade.name, relation))


    def _get_field_info(self, fields):
        field_names = []
        field_labels = []

        for field in fields:
            if isinstance(field, (list, tuple)):
                field_names.append(field[0])
                field_labels.append(field[1])
            else:
                field_names.append(field)
                field_labels.append(field)
        
        return (field_names, field_labels)