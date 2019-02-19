from django.conf import settings
from django.core.management.base import CommandError
from django.db.models import fields
from django.utils.timezone import now

from utility import query


class ScopeException(CommandError):
    pass


class ModelFacade:

    thread_lock = settings.DB_LOCK

    
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

        self._scope = {}

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

    def set_scope(self, **filters):
        self._scope = filters

    def _check_scope(self, filters):
        scope = self.scope()

        if scope is False:
            raise ScopeException("Scope missing from {} query".format(self.model.__name__))

        for filter, value in scope.items():
            if not filter in filters:
                filters[filter] = value

        for filter, value in self._scope.items():
            if not filter in filters:
                filters[filter] = value


    def query(self, **filters):
        with self.thread_lock:
            self._check_scope(filters)

            if not filters:
                return self.model.objects.all().distinct()
        
            return self.model.objects.filter(**filters).distinct()

    def all(self):
        return self.query()

    def filter(self, **filters):
        return self.query(**filters)


    def keys(self, **filters):
        queryset = self.query(**filters)
        with self.thread_lock:
            return queryset.values_list(self.key(), flat = True)

    def field_values(self, name, **filters):
        queryset = self.query(**filters)
        with self.thread_lock:
            return queryset.values_list(name, flat = True)

    def values(self, *fields, **filters):
        if not fields:
            fields = self.fields

        queryset = self.query(**filters)
        with self.thread_lock:
            return queryset.values(*fields)

    def count(self, **filters):
        queryset = self.query(**filters)
        with self.thread_lock:
            return queryset.count()
    
    def related(self, key, relation, **filters):
        instance = self.retrieve(key)
        queryset = None
        
        if instance:
            with self.thread_lock:
                queryset = query.get_queryset(instance, relation)

                if queryset:
                    if filters:
                        queryset = queryset.filter(**filters).distinct()
                    else:
                        queryset = queryset.all()
        
        return queryset


    def retrieve(self, key, **filters):
        with self.thread_lock:
            self._check_scope(filters)

            data = None
            try:
                filters[self.key()] = key
                data = self.model.objects.get(**filters)
        
            except self.model.DoesNotExist:
                return None
        
            except self.model.MultipleObjectsReturned:
                raise ScopeException("Scope missing from {} {} retrieval".format(self.model.__name__, key))    

            return data


    def create(self, key, **values):
        with self.thread_lock:
            values[self.key()] = key
            self._check_scope(values)
            return self.model(**values)

    def store(self, key, **values):
        with self.thread_lock:
            filters = { self.key(): key }
            self._check_scope(filters)

            instance, created = self.model.objects.get_or_create(**filters)

            for field, value in values.items():
                setattr(instance, field, value)

        instance.save()
        return (instance, created)

    def delete(self, key, **filters):
        filters[self.key()] = key
        return self.clear(**filters)

    def clear(self, **filters):
        queryset = self.query(**filters)
        with self.thread_lock:
            deleted, del_per_type = queryset.delete()

            if deleted:
                return True
            return False 


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
