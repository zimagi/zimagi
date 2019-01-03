
from django.db.models import fields
from django.utils.timezone import now

from utility import query
from .errors import ScopeException


class ModelFacade:
    
    def __init__(self, cls):
        self.model = cls
        self.name = cls.__name__.lower()
        
        self.pk = self.model._meta.pk.name
        self.required = []
        self.optional = []
        self.fields = [self.pk]
        post_fields = []

        if self.pk != self.key():
            self.fields.append(self.key())

        scope = self.scope(True)
        if scope:
            for field in scope:
                self.fields.append(field)    

        for field in self.model._meta.fields:
            if field.name != self.pk and field.name != self.key():
                self.optional.append(field.name)

                if (not field.null 
                    and field.blank == False
                    and field.default == fields.NOT_PROVIDED):
                    self.required.append(field.name)

            if field.name in ['created', 'updated']:
                post_fields.append(field.name)
            elif field.name not in self.fields:
                self.fields.append(field.name)

        for field in post_fields:
            self.fields.append(field)


    def get_packages(self):
        return ['all']


    def key(self):
        # Override in subclass if model is scoped
        return self.pk

    def scope(self, fields = False):
        # Override in subclass
        #
        # Three choices: (non fields)
        # 1. Empty dictionary equals no filters
        # 2. Dictionary items are extra filters
        # 3. False means ABORT access/update attempt
        #
        if fields:
            return []
        return {}

    def _check_scope(self, filters):
        scope = self.scope()

        if scope is False:
            raise ScopeException("Scope missing from {} query".format(self.model.__name__))

        for filter, value in scope.items():
            if not filter in filters:
                filters[filter] = value


    def query(self, **filters):
        self._check_scope(filters)

        if not filters:
            return self.model.objects.all().distinct()
        
        return self.model.objects.filter(**filters).distinct()

    def all(self):
        return self.query()

    def filter(self, **filters):
        return self.query(**filters)


    def keys(self, **filters):
        return self.query(**filters).values_list(self.key(), flat = True)

    def field_values(self, name, **filters):
        return self.query(**filters).values_list(name, flat = True)

    def values(self, *fields, **filters):
        if not fields:
            fields = self.fields

        return self.query(**filters).values(*fields)

    def count(self, **filters):
        return self.query(**filters).count()
    
    def related(self, key, relation, **filters):
        queryset = None
        instance = self.retrieve(key)

        if instance:
            queryset = query.get_queryset(instance, relation)

            if queryset:
                if filters:
                    queryset = queryset.filter(**filters).distinct()
                else:
                    queryset = queryset.all()
                
        return queryset


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


    def render(self, fields, queryset_values):
        fields = list(fields)
        data = [fields]

        for item in queryset_values:
            record = []

            for field in fields:
                if field in ['created', 'updated'] and item[field]:
                    value = item[field].strftime("%Y-%m-%d %H:%M:%S %Z")
                else:
                    value = item[field]

                record.append(value)

            data.append(record)

        return data

    def render_values(self, *fields, **filters):
        return self.render(fields, self.values(*fields, **filters))
