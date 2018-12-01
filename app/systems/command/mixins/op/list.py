
class ListMixin(object):
    
    def exec_list(self, facade, *fields, **filters):
        if facade.count():
            self.print_table(facade.render_values(*fields, **filters))


    def exec_processed_list(self, facade, process_func, *fields, **filters):
        if facade.count():
            data = facade.render(facade.values(*fields, **filters))
            key_index = data[0].index(facade.key())

            for index, info in enumerate(data):
                if index == 0:
                    process_func('label', info, key_index)
                else:
                    process_func('data', info, key_index)

            self.print_table(data)


    def exec_list_related(self, facade, key, relation, *fields, **filters):
        queryset = facade.related(key, relation, **filters)
        
        if queryset:
            self.print_table(facade.render(queryset.values(), *fields))
