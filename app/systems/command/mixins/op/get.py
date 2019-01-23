from .base import OpMixin

import json


class GetMixin(OpMixin):

    def exec_get(self, facade, key):
        instance = self.get_instance(facade, key, error_on_not_found = False)
        
        if instance:
            data = []

            for field in facade.fields:
                if field[0] != '_':
                    value = getattr(instance, field, None)

                    try:
                        json.dumps(value)
                    except Exception:
                        value = str(value)

                    if field == 'config':
                        value = json.dumps(value, indent = 2)

                    if field not in ['created', 'updated']:
                        data.append([field, value])

            data.append([
                'created', 
                instance.created.strftime("%Y-%m-%d %H:%M:%S %Z")
            ])
            if instance.updated:
                data.append([
                    'updated', 
                    instance.updated.strftime("%Y-%m-%d %H:%M:%S %Z")
                ])

            self.table(data)
        else:
            self.error("{} does not exist".format(facade.name.title()))
