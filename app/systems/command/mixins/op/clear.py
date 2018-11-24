
class ClearMixin(object):

    def exec_clear(self, facade):
        if facade.count():
            self.confirmation(self.color("Are you sure you want to clear ALL {} instances?".format(facade.name), 'notice'))
        else:
            self.warning("No {} instances exist".format(facade.name))

        self.info("Clearing all {} instances".format(facade.name))
        
        if facade.clear():
            self.success(" > Successfully cleared {} instances".format(facade.name))
        else:
            self.error("{} deletion failed".format(facade.name.title()))
