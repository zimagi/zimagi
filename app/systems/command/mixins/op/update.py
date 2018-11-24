
class UpdateMixin(object):

    def exec_update(self, facade, name):
        self.data("Updating {}".format(facade.name), name)
        
        instance, created = facade.store(name)
        
        if instance:
            self.success(" > Successfully updated {}".format(facade.name))
        else:
            self.error("{} update failed".format(facade.name.title()))
