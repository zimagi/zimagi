
from utility import query


class AddMixin(object):
    
    def exec_add(self, facade, key, fields = {}): 
        for field in fields.keys():
            if field not in facade.fields:
                self.error("Given field {} is not in {}".format(field, facade.name))

        instance, created = facade.store(key, **fields)
        
        if instance:
            if created:
                self.success("Successfully created {}".format(facade.name))
            else:
                self.warning("{} already exists".format(facade.name.title()))
        else:
            self.error("{} creation failed".format(facade.name.title()))


    def exec_add_related(self, facade, instance, relation, keys, **fields):
        for field in fields.keys():
            if field not in facade.fields:
                self.error("Given field {} is not in {}".format(field, facade.name))

        queryset = query.get_queryset(instance, relation)
        instance_name = type(instance).__name__.lower()

        if queryset:
            for key in keys:
                sub_instance, created = facade.store(key, **fields)

                if sub_instance:
                    try:
                        queryset.add(sub_instance)
                    except Exception:
                        self.error("{} add failed".format(facade.name.title()))

                    self.success("Successfully added {} to {}".format(key, str(instance)))
                else:
                    self.error("{} {} creation failed".format(facade.name.title(), key))
        else:
            self.error("There is no relation {} on {} class".format(relation, instance_name))
