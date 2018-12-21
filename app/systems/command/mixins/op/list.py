
class ListMixin(object):
    
    def exec_list(self, facade, *fields, **filters):
        if facade.count():
            self.table(facade.render_values(*fields, **filters), '{}_list'.format(facade.name))


    def exec_processed_list(self, facade, process_func, *fields, **filters):
        if facade.count():
            data = facade.render(facade.values(*fields, **filters))
            key_index = data[0].index(facade.key())

            for index, info in enumerate(data):
                if index == 0:
                    process_func('label', info, key_index)
                else:
                    process_func('data', info, key_index)

            self.table(data, '{}_list'.format(facade.name))


    def exec_list_related(self, facade, key, relation, relation_facade, *fields, **filters):
        queryset = facade.related(key, relation, **filters)
        
        if queryset:
            self.table(relation_facade.render(queryset.values(*fields)), '{}_{}_list'.format(facade.name, relation))
