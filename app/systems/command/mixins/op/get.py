
class GetMixin(object):

    def exec_get(self, facade, key):
        instance = facade.retrieve(key)
        
        if instance:
            data = []

            for field in facade.fields:
                if field not in ['created', 'updated']:
                    data.append([
                        field, 
                        getattr(instance, field, '')
                    ])

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
