from .base import OpMixin

import json


class GetMixin(OpMixin):

    def exec_get(self, facade, key):
        instance = self.get_instance(facade, key, required = False)
        
        if instance:
            data = []
            for field in facade.get_display_fields():
                if field[0] == '-':
                    data.append((' ', ' '))
                else:
                    display_method = getattr(facade, "get_field_{}_display".format(field), None)
                    value = getattr(instance, field, None)

                    if display_method and callable(display_method):
                        label, value = display_method(value)
                        label = "{} ({})".format(label, field)
                    else:
                        value = str(value)
                        label = field
                
                    data.append((label, value))

            self.table(data)
        else:
            self.error("{} does not exist".format(facade.name.title()))
