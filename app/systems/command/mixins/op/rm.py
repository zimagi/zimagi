
from utility import query


class RemoveMixin(object):

    def exec_rm(self, facade, name, prompt = True):
        if facade.retrieve(name):
            if prompt:
                self.confirmation(self.data("Are you sure you want to remove {}".format(facade.name), name, 'notice', False))
        else:
            self.warning("{} does not exist".format(facade.name.title()))

        if facade.delete(name):
            self.success(" > Successfully deleted {}".format(facade.name))
        else:
            self.error("{} deletion failed".format(facade.name.title()))


    def exec_rm_related(self, facade, instance, relation, keys, prompt = True):
        queryset = query.get_queryset(instance, relation)
        instance_name = type(instance).__name__.lower()

        if queryset:
            if prompt:
                self.confirmation(self.data("Are you sure you want to remove {} {}".format(str(instance), facade.name), ", ".join(keys), 'notice', False))
    
            for key in keys:
                sub_instance = facade.retrieve(key)

                if sub_instance:
                    try:
                        queryset.remove(sub_instance)
                    except Exception:
                        self.error("{} remove failed".format(facade.name.title()))

                    self.success(" > Successfully removed {} from {}".format(key, str(instance)))
                else:
                    self.error("{} {} does not exist".format(facade.name.title(), key))
        else:
            self.error("There is no relation {} on {} class".format(relation, instance_name))
   