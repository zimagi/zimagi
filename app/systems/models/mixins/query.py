from functools import lru_cache

from ..errors import ScopeError
from ..parsers.fields import FieldProcessor
from ..parsers.order import OrderParser
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
            self._order = ensure_list(order)
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


    def get_field_processors(self):
        return self._field_processors


    def filter(self, **filters):
        return self._query('filter', filters)

    def exclude(self, **filters):
        return self._query('exclude', filters)


    @property
    def qs(self):
        return self.model.objects.all()

    def all(self):
        return self.filter()


    def keys(self, queryset_function = None, **filters):
        return self._get_values_list(self.key(), queryset_function, filters)

    def field_values(self, name, queryset_function = None, **filters):
        return self._get_values_list(name, queryset_function, filters)


    def values(self, *fields, queryset_function = None, **filters):
        queryset, query_fields, processors = self._get_field_query(fields, queryset_function, filters)
        return queryset.values(*query_fields)

    def dataframe(self, *fields, queryset_function = None, **filters):
        queryset, query_fields, processors = self._get_field_query(fields, queryset_function, filters)
        dataframe = pandas.DataFrame.from_records(queryset.values_list(*query_fields), columns = query_fields)

        for processor in processors:
            dataframe[processor.name] = self.get_provider('field_processor', processor.provider).exec(
                dataframe,
                dataframe[processor.field],
                *processor.args,
                **processor.options
            )

        for field in self.intermediate_fields:
            dataframe.drop(field, axis = 1, inplace = True)

        return dataframe


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


    def parse_order(self, fields):
        order_fields = []

        if fields:
            with self.thread_lock:
                parser = OrderParser(self)

                for field in ensure_list(fields):
                    field = re.sub(r'\.+', '__', field)

                    match = re.match(r'^\((.+)\)$', field.strip())
                    if match:
                        field = match[1]

                    order_fields.append(parser.evaluate(field))

        return order_fields


    def _query(self, manager_method, filters, fields = None):
        self._check_scope(filters)

        manager = self.model.objects
        filters = self.parse_filters(filters)
        order   = self.parse_order(self._order)

        annotations = self.get_annotations()
        if annotations:
            for name, value in annotations.items():
                try:
                    if fields and name in fields:
                        manager = manager.annotate(**{ name: value })
                    else:
                        manager = manager.alias(**{ name: value })

                except ValueError:
                    # Already exists
                    pass

        if not filters:
            queryset = manager.all()
        else:
            queryset = getattr(manager, manager_method)(filters)

        if order:
            queryset = queryset.order_by(*order)

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

    def _get_field_query(self, fields, queryset_function, filters, manager_method = 'filter'):
        if not fields:
            fields = self.fields

        fields = self.parse_fields(fields)
        query_fields = []
        processors   = []

        for field in fields:
            if isinstance(field, FieldProcessor):
                processors.append(field)
            else:
                query_fields.append(field)

        queryset = self._query(manager_method, filters, fields)

        if queryset_function:
            queryset = queryset_function(queryset)

        return (queryset, query_fields, processors)
