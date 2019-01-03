from .base import OpMixin


class UpdateMixin(OpMixin):

    def exec_update(self, facade, name, fields = {}):
        for field in fields.keys():
            if field not in facade.fields:
                self.error("Given field {} is not in {} (available: {})".format(field, facade.name, ", ".join(facade.fields)))

        instance, created = facade.store(name, **fields)
        
        if instance:
            self.success("Successfully updated {} {}".format(facade.name, name))
        else:
            self.error("{} {} update failed".format(facade.name.title(), name))

        return instance


    def exec_update_related(self, facade, instance, relation, keys, **fields):
        for field in fields.keys():
            if field not in facade.fields:
                self.error("Given field {} is not in {} (available: {})".format(field, facade.name, ", ".join(facade.fields)))

        queryset = query.get_queryset(instance, relation)
        instance_name = type(instance).__name__.lower()

        if queryset:
            for key in keys:
                sub_instance, created = facade.store(key, **fields)

                if sub_instance:
                    try:
                        queryset.add(sub_instance)
                    except Exception:
                        self.error("{} update failed".format(facade.name.title()))

                    self.success("Successfully updated {} to {}".format(key, str(instance)))
                else:
                    self.error("{} {} update failed".format(facade.name.title(), key))
        else:
            self.error("There is no relation {} on {} class".format(relation, instance_name))
