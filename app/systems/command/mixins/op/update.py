
class UpdateMixin(object):

    def exec_update(self, facade, name, fields = {}):
        for field in fields.keys():
            if field not in facade.fields:
                self.error("Given field {} is not in {}".format(field, facade.name))

        self.data("Updating {}".format(facade.name), name)
        instance, created = facade.store(name, **fields)
        
        if instance:
            self.success(" > Successfully updated {}".format(facade.name))
        else:
            self.error("{} update failed".format(facade.name.title()))
