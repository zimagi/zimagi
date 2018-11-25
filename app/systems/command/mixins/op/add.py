
class AddMixin(object):
    
    def exec_add(self, facade, name, fields = {}): 
        for field in fields.keys():
            if field not in facade.fields:
                self.error("Given field {} is not in {}".format(field, facade.name))

        self.data("Creating {}".format(facade.name), name)
        instance, created = facade.store(name, **fields)
        
        if instance:
            if created:
                self.success(" > Successfully created {}".format(facade.name))
            else:
                self.warning("{} already exists".format(facade.name.title()))
        else:
            self.error("{} creation failed".format(facade.name.title()))
