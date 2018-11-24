
from .errors import ScopeException


class ModelFacade:
    
    def __init__(self, cls, meta_cls):
        self.model = cls
        self.name = cls.__name__.lower()
        self.meta = meta_cls

        self.pk = self.model._meta.pk.name
        self.fields = []

        for field in self.model._meta.fields:
            self.fields.append(field.name)


    def key(self):
        # Override in subclass if model is scoped
        return self.pk

    def scope(self):
        # Override in subclass
        #
        # Three choices:
        # 1. Empty dictionary equals no filters
        # 2. Dictionary items are extra filters
        # 3. False means ABORT access/update attempt
        #
        return {}

    def _check_scope(filters):
        scope = self.scope()

        if scope is False:
            raise ScopeException("Scope missing from {} query".format(self.model.__name__))

        for filter, value in scope.items():
            filters[filter] = value


    def query(self, **filters):
        self._check_scope(filters)

        if not filters:
            return self.model.objects.all().distinct()
        
        return self.model.objects.filter(**filters).distinct()


    def keys(self, **filters):
        return list(self.query(**filters).values_list(self.key(), flat = True))

    def field_values(self, name, **filters):
        return list(self.query(**filters).values_list(name, flat = True))

    def values(self, *fields, **filters):
        if not fields:
            fields = self.fields
        
        return list(self.query(**filters).values_list(fields))

    def count(self, **filters):
        return self.query(**filters).count()


    def retrieve(self, key, **filters):
        self._check_scope(filters)

        try:
            filters[self.key()] = key
            data = self.model.objects.get(**filters)
        except self.model.DoesNotExist:
            return None

        return data

    def store(self, key, **values):
        filters = { self.key(): key }
        self._check_scope(filters)

        instance, created = self.model.objects.get_or_create(**filters)

        if created:
            instance.created = now()
        else:
            instance.updated = now()

        for field, value in values.items():
            setattr(instance, field, value)

        instance.save()
        return (instance, created)

    def clear(self, **filters):
        deleted, del_per_type = self.query(**filters).delete()

        if deleted:
            return True
        return False 

    def delete(self, key, **filters):
        filters[self.key()] = key
        return self.clear(**filters)


    def render(self, *fields, **filters):
        if not fields:
            fields = self.fields
        
        data = [fields]

        for item in self.values(*fields, **filters):
            record = []

            for field in fields:
                if field in ['created', 'updated'] and item[field]:
                    value = item[field].strftime("%Y-%m-%d %H:%M:%S %Z")
                else:
                    value = item[field]

                record.append(value)

            data.append(record)

        return data
