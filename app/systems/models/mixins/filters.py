from functools import lru_cache

from django.db.models import Q

from ..parsers.filters import FilterParser
from ..parsers.function import FunctionParser

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


    def parse_filters(self, filters):
        filter_parser   = FilterParser(self)
        function_parser = FunctionParser(self)

        def _parse_filter_value(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    value[key] = _parse_filter_value(item)
            elif isinstance(value, (list, tuple)):
                for index, item in enumerate(value):
                    value[index] = _parse_filter_value(item)
            else:
                match = re.match(r'^\((.+)\)$', str(value).strip())
                if match:
                    value = filter_parser.evaluate(match[1])

            return value

        def _check_function(field):
            if ':' in field:
                match = re.match(r'^([^\:]+\:[A-Z][A-Z0-9\_]+[A-Z0-9](?:\(.+\))?)(\_\_[a-z]+$|$)', field.strip())
                return ( match[1], match[2] )
            return None

        def _parse_filter(filter_group, joiner = 'AND', negate = False):
            query_filter = Q()

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
                        function = _check_function(field[1:])
                        if function:
                            field = function_parser.evaluate(function[0])
                            field = "{}{}".format(field, function[1]) if function[1] else field
                        else:
                            field = field[1:]

                        filter = ~Q(**{ field: value })
                    else:
                        function = _check_function(field)
                        if function:
                            field = function_parser.evaluate(function[0])
                            field = "{}{}".format(field, function[1]) if function[1] else field

                        filter = Q(**{ field: value })

                if filter:
                    if joiner == 'OR':
                        query_filter |= filter
                    else:
                        query_filter &= filter

            return ~query_filter if negate else query_filter

        return _parse_filter(filters)
