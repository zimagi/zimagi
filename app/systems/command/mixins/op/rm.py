from .base import OpMixin
from utility import query


class RemoveMixin(OpMixin):

    def exec_rm(self, facade, name, display_warning = True):
        instance = self.get_instance(facade, name, required = False)

        if not instance:
            if display_warning:
                self.warning("{} does not exist".format(facade.name.title()))
        else:
            if facade.delete(name):
                self.success("Successfully deleted {} {}".format(facade.name, name))
            else:
                self.error("{} {} deletion failed".format(facade.name.title(), name))

        return instance


    def exec_rm_related(self, facade, instance, relation, keys, display_warning = True):
        queryset = query.get_queryset(instance, relation)
        instance_name = type(instance).__name__.lower()

        if queryset:
            for key in keys:
                sub_instance = self.get_instance(facade, key, required = False)

                if sub_instance:
                    try:
                        queryset.remove(sub_instance)
                    except Exception:
                        self.error("{} remove failed".format(facade.name.title()))

                    self.success("Successfully removed {} from {}".format(key, str(instance)))
                else:
                    if display_warning:
                        self.warning("{} {} does not exist".format(facade.name.title(), key))
        else:
            self.error("There is no relation {} on {} class".format(relation, instance_name))
   