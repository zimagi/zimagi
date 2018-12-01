
class GetMixin(object):

    def exec_get(self, facade, key):
        instance = facade.retrieve(key)
        
        if instance:
            data = []

            for field in facade.fields:
                if field not in ['created', 'updated']:
                    data.append([
                        field, 
                        self.color(getattr(instance, field, ''))
                    ])

            data.append([
                'created', 
                self.color(instance.created.strftime("%Y-%m-%d %H:%M:%S %Z"))
            ])
            if instance.updated:
                data.append([
                    'updated', 
                    self.color(instance.updated.strftime("%Y-%m-%d %H:%M:%S %Z"))
                ])

            self.print_table(data)
        else:
            self.warning("{} does not exist".format(facade.name.title()))
