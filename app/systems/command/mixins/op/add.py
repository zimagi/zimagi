
class AddMixin(object):
    
    def exec_add(self, facade, name):
        self.data("Creating {}".format(facade.name), name)
        
        instance, created = facade.store(name)
        
        if instance:
            if created:
                self.success(" > Successfully created {}".format(facade.name))
            else:
                self.warning("{} already exists".format(facade.name.title()))
        else:
            self.error("{} creation failed".format(facade.name.title()))
