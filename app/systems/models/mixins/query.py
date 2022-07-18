from ..errors import ScopeError
from utility.data import ensure_list, get_identifier

import pandas
import re


class ModelFacadeQueryMixin(object):

    def __init__(self):
        super().__init__()

        self._order = None
        self._limit = None

        self._scope = {}


    def set_order(self, order):
        if order:
            self._order = [
                re.sub(r'^~', '-', x) for x in ensure_list(order)
            ]
        else:
            self._order = None

        return self

    def set_limit(self, limit):
        self._limit = limit
        return self


    def set_scope(self, filters):
        self._scope = filters
        return self

    def get_scope(self):
        return self._scope

    def get_scope_name(self):
        return get_identifier([ value for key, value in self.get_scope().items() ])


    def _check_scope(self, filters):
        for filter, value in self.get_scope().items():
            if not filter in filters:
                filters[filter] = value


    def filter(self, **filters):
        return self._query('filter', filters)

    def exclude(self, **filters):
        return self._query('exclude', filters)


    def all(self):
        return self.filter()


    def keys(self, queryset_function = None, **filters):
        return self._get_values_list(self.key(), queryset_function, filters)

    def field_values(self, name, queryset_function = None, **filters):
        return self._get_values_list(name, queryset_function, filters)


    def values(self, *fields, queryset_function = None, **filters):
        queryset, fields = self._get_field_query(fields, queryset_function, filters)
        return queryset.values(*fields)


    def dataframe(self, *fields, queryset_function = None, **filters):
        queryset, fields = self._get_field_query(fields, queryset_function, filters)
        return pandas.DataFrame.from_records(queryset.values_list(*fields), columns = fields)


    def count(self, queryset_function = None, **filters):
        queryset = self._get_basic_query(queryset_function, filters)
        return queryset.count()


    def retrieve_by_id(self, id):
        filters = {}
        try:
            filters[self.pk] = id
            data = self.model.objects.filter(**filters).get()

        except self.model.DoesNotExist:
            return None
        return data

    def retrieve(self, key, **filters):
        self._check_scope(filters)
        try:
            filters[self.key()] = key
            data = self.model.objects.filter(**filters).get()

        except self.model.DoesNotExist:
            return None

        except self.model.MultipleObjectsReturned:
            raise ScopeError("Scope missing from {} {} retrieval".format(self.name, key))

        return data

    def exists(self, key, **filters):
        self._check_scope(filters)
        filters[self.key()] = key
        return self.model.objects.filter(**filters).exists()


    def _query(self, manager_method, filters):
        self._check_scope(filters)

        manager = self.model.objects
        filters = self._parse_filters(filters)

        if self.check_annotations():
            manager = manager.annotate(**self.get_annotations())

        if not filters:
            queryset = manager.all()
        else:
            queryset = getattr(manager, manager_method)(filters)

        if self._order:
            queryset = queryset.order_by(*self._order)

        if self._limit:
            queryset = queryset[:self._limit]

        return queryset

    def _get_values_list(self, field_name, queryset_function, filters):
        queryset = self.filter(**filters)

        if queryset_function:
            queryset = queryset_function(queryset)

        return queryset.values_list(field_name, flat = True)


    def _get_basic_query(self, queryset_function, filters):
        queryset = self.filter(**filters)

        if queryset_function:
            queryset = queryset_function(queryset)

        return queryset

    def _get_field_query(self, fields, queryset_function, filters):
        if not fields:
            fields = self.fields

        fields   = self._parse_fields(fields)
        queryset = self.filter(**filters)

        if queryset_function:
            queryset = queryset_function(queryset)

        return (queryset, fields)
