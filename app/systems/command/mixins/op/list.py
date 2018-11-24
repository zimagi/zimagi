
class ListMixin(object):
    
    def exec_list(self, facade):
        self.print_table(facade.render())
