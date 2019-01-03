from .base import OpMixin
from utility import query


class RemoveMixin(OpMixin):

    def exec_rm(self, facade, name):
        instance = facade.retrieve(name)

        if not instance:
            self.warning("{} does not exist".format(facade.name.title()))
        else:
            if facade.delete(name):
                self.success("Successfully deleted {} {}".format(facade.name, name))
            else:
                self.error("{} {} deletion failed".format(facade.name.title(), name))

        return instance


    def exec_rm_related(self, facade, instance, relation, keys):
        queryset = query.get_queryset(instance, relation)
        instance_name = type(instance).__name__.lower()

        if queryset:
            for key in keys:
                sub_instance = facade.retrieve(key)

                if sub_instance:
                    try:
                        queryset.remove(sub_instance)
                    except Exception:
                        self.error("{} remove failed".format(facade.name.title()))

                    self.success("Successfully removed {} from {}".format(key, str(instance)))
                else:
                    self.error("{} {} does not exist".format(facade.name.title(), key))
        else:
            self.error("There is no relation {} on {} class".format(relation, instance_name))
   