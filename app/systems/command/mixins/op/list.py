
class ListMixin(object):
    
    def exec_list(self, facade, *fields, **filters):
        if facade.count():
            self.print_table(facade.render_values(*fields, **filters))


    def exec_list_related(self, facade, key, relation, *fields, **filters):
        queryset = facade.related(key, relation, **filters)
        
        if queryset:
            self.print_table(facade.render(queryset.values(), *fields))
