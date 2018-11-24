
class RemoveMixin(object):

    def exec_rm(self, facade, name):
        if facade.retrieve(name):
            self.confirmation(self.data("Are you sure you want to remove {}".format(facade.name), name, 'notice', False))
        else:
            self.warning("{} does not exist".format(facade.name.title()))

        self.data("Removing {}".format(facade.name), name, 'notice')
        
        if facade.delete(name):
            self.success(" > Successfully deleted {}".format(facade.name))
        else:
            self.error("{} deletion failed".format(facade.name.title()))
    