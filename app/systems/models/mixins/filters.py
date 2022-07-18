from functools import lru_cache

from django.db.models import Q

from ..parsers.filters import FilterParser

import re


class ModelFacadeFilterMixin(object):

    @lru_cache(maxsize = None)
    def get_scope_filters(self, instance):
        filters = {}

        for name in self.scope_fields:
            scope = getattr(instance, name, None)
            if scope:
                filters[name] = scope.name
                for name, value in scope.facade.get_scope_filters(scope).items():
                    filters[name] = value
        return filters


    def _parse_filters(self, filters):
        parser = FilterParser(self)

        def _parse_filter_value(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    value[key] = _parse_filter_value(item)
            elif isinstance(value, (list, tuple)):
                for index, item in enumerate(value):
                    value[index] = _parse_filter_value(item)

            if isinstance(value, str):
                match = re.match(r'^\((.+)\)$', value.strip())
                if match:
                    value = parser.evaluate(match[1])

            return value

        def _parse_filter(filter_group, joiner = 'AND', negate = False):
            query_filter = ~Q() if negate else Q()

            if not filter_group or not isinstance(filter_group, dict):
                return query_filter

            for field, value in filter_group.items():
                filter = None

                if re.match(r'^[\~\-]?AND([\_\-][A-Za-z0-9\_\-]+)?$', field):
                    filter = _parse_filter(value, negate = (field[0] in ('~', '-')))
                elif re.match(r'^[\~\-]?OR([\_\-][A-Za-z0-9\_\-]+)?$', field):
                    filter = _parse_filter(value, joiner = 'OR', negate = (field[0] in ('~', '-')))
                else:
                    field = re.sub(r'\.+', '__', field)
                    value = _parse_filter_value(value)
                    if field[0] in ('~', '-'):
                        filter = ~Q(**{ field[1:]: value })
                    else:
                        filter = Q(**{ field: value })

                if filter:
                    if joiner == 'OR':
                        query_filter |= filter
                    else:
                        query_filter &= filter

            return query_filter

        return _parse_filter(filters)
