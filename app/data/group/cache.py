
class Cache(object):

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self):
        if not getattr(self, '_initialized', False):
            self.data = {}
            self._initialized = True


    def map(self, facade):
        facade_groups = {}

        for result in facade.values(facade.pk, 'groups__name'):
            if result['groups__name']:
                if result[facade.pk] in facade_groups:
                    facade_groups[result[facade.pk]].append(result['groups__name'])
                else:
                    facade_groups[result[facade.pk]] = [result['groups__name']]

            elif not facade_groups.get(result[facade.pk], None):
                facade_groups[result[facade.pk]] = []

        return facade_groups


    def get(self, facade, id, reset = False):
        if reset or not self.data.get(facade.name, None):
            self.data[facade.name] = self.map(facade)
        return self.data[facade.name].get(id, [])

    def clear(self, facade):
        self.data.pop(facade.name, None)
