
class GetMixin(object):

    def exec_get(self, facade, name):
        instance = facade.retrieve(name)
        
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
                self.color(state.created.strftime("%Y-%m-%d %H:%M:%S %Z"))
            ])
            if state.updated:
                data.append([
                    'updated', 
                    self.color(state.updated.strftime("%Y-%m-%d %H:%M:%S %Z"))
                ])

            self.print_table(data)
        else:
            self.warning("{} does not exist".format(facade.name.title()))
