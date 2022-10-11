from functools import lru_cache

from django.conf import settings
from django.utils.encoding import force_str
from rest_framework.filters import BaseFilterBackend, SearchFilter, OrderingFilter
from django_filters.rest_framework.backends import DjangoFilterBackend

from .filters import annotated_query, JSONFilter
from .related import RelatedFilterSet
from utility.data import load_json, rank_similar

import re


def get_parameters(request, action, view):
    parameters = {}
    json_fields = []

    for parameter_info in view.schema.get_filter_parameters(request.path, action):
        if parameter_info['in'] == 'query':
            parameters[parameter_info['name']] = parameter_info['schema']['type']
            if 'x-json' in parameter_info['schema']:
                json_fields.append(parameter_info['name'])

    return parameters, json_fields


def check_json_field(json_fields, parameter):
    for name in json_fields:
        if parameter.startswith(name):
            return True
    return False


class FilterValidationMixin(object):

    def check_parameter_errors(self, view, request, action, facade):
        # Override in subclass
        return None


class FieldValidationMixin(FilterValidationMixin):

    @lru_cache(maxsize = None)
    def get_fields(self, view, request, action):
        fields = {}
        for parameter_info in view.schema.get_filter_parameters(request.path, action):
            if parameter_info['in'] == 'query':
                if 'x-field' in parameter_info['schema'] and parameter_info['name'] == parameter_info['schema']['x-field']:
                    fields[parameter_info['schema']['x-field']] = parameter_info['schema']['type']
        return fields


class RelatedFilterBackend(FilterValidationMixin, DjangoFilterBackend):

    filterset_base = RelatedFilterSet


    def get_schema_operation_parameters(self, view):
        queryset = view.get_queryset()
        filterset_class = self.get_filterset_class(view, queryset)

        if not filterset_class:
            return []

        parameters = []
        for field_name, field in filterset_class.base_filters.items():
            field_components = field_name.split(':')
            base_field_name = field_components[0]
            name_components = base_field_name.split('__')

            parameter = {
                'name': field_name,
                'required': field.extra['required'],
                'in': 'query',
                'description': "{}: {}".format(queryset.model.__name__, field_name),
                'schema': {
                    'type': field.label,
                    'x-field': base_field_name
                }
            }
            if field_name == field.field_name:
                if field.field_name == view.facade.pk:
                    parameter['schema']['x-id'] = True
                if field.field_name == view.facade.key():
                    parameter['schema']['x-key'] = True

            if getattr(field, 'lookup_expr', None) and field.lookup_expr:
                parameter['schema']['x-lookup'] = field.lookup_expr

            if field.extra and 'choices' in field.extra:
                parameter['schema']['enum'] = [ choice[0] for choice in field.extra["choices"]]

            if len(field_components) > 1:
                aggregator = field_components[-1].split('__')[0]
                parameter['schema']['x-aggregator'] = aggregator
            if len(name_components) > 1:
                parameter['schema']['x-base-field'] = name_components[0]

            if isinstance(field, JSONFilter):
                parameter['schema']['x-json'] = True

            parameters.append(parameter)

        return parameters


    def check_parameter_errors(self, view, request, action, facade):
        parameters, json_fields = get_parameters(request, action, view)
        not_found  = []

        if action == 'list':
            parameters[view.pagination_class.page_query_param] = 'number'
            parameters[view.pagination_class.page_size_query_param] = 'number'

        for parameter in request.query_params.keys():
            parameter = parameter.strip()

            if parameter == 'schema':
                schema = view.schema.get_operation(request.path, action)
                if schema:
                    schema['description'] = request.path
                    schema['components'] = view.schema.get_components(request.path, action)
                    return schema
                else:
                    parameter = 'help'

            if parameter == 'help':
                return {
                    'detail': 'API parameter help',
                    'parameters': parameters
                }

            if parameter[0] == '-':
                parameter = parameter[1:]

            if parameter not in parameters and not check_json_field(json_fields, parameter):
                not_found.append({
                    'field': parameter,
                    'similar': rank_similar(parameters.keys(), parameter, data = parameters)
                })

        if not_found:
            return {
                'detail': 'Requested filter parameters not found',
                'not_found': not_found
            }
        return None


class CompoundFilterBackend(FilterValidationMixin, BaseFilterBackend):

    compound_title = 'Compound Filter'
    compound_description = 'URL encoded JSON object of related filters'
    compound_operator = r'^[\-]?(OR|AND)([\_\-][A-Za-z0-9\_\-]+)?$'


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters = {}


    def filter_queryset(self, request, queryset, view):
        if self.filters:
            filters = queryset.model.facade.parse_filters(self.filters)
            queryset = annotated_query(queryset).filter(filters)

        return queryset


    def get_schema_operation_parameters(self, view):
        return [
            {
                'name': 'AND[_??]',
                'required': False,
                'in': 'query',
                'description': force_str(self.compound_description),
                'schema': {
                    'type': 'json<lookup:[(]value[)]>'
                }
            },
            {
                'name': 'OR[_??]',
                'required': False,
                'in': 'query',
                'description': force_str(self.compound_description),
                'schema': {
                    'type': 'json<lookup:[(]value[)]>'
                }
            }
        ]

    def check_parameter_errors(self, view, request, action, facade):
        errors = []

        for parameter, value in request.query_params.items():
            if re.match(self.compound_operator, parameter):
                try:
                    self.filters[parameter] = load_json(value)

                except Exception as e:
                    errors.append({
                        'compound filter': parameter,
                        'error': str(e)
                    })
        if errors:
            return { 'detail': 'Compound filter errors', 'errors': errors }
        return None


class FieldSelectFilterBackend(FieldValidationMixin, BaseFilterBackend):

    fields_param = settings.FIELDS_PARAM
    fields_title = 'Fields'
    fields_description = 'Comma separated list of fields to return'


    def filter_queryset(self, request, queryset, view):
        fields = request.query_params.get(self.fields_param, None)
        request_fields = self._get_request_fields(
            queryset.model.facade,
            fields
        )
        if request_fields:
            request_fields = queryset.model.facade.parse_fields(request_fields)
            return annotated_query(queryset, request_fields).values(*request_fields)
        return queryset


    def get_schema_operation_parameters(self, view):
        return [
            {
                'name': self.fields_param,
                'required': False,
                'in': 'query',
                'description': force_str(self.fields_description),
                'schema': {
                    'type': 'csv<[(]string[)]>'
                }
            }
        ]

    def check_parameter_errors(self, view, request, action, facade):
        parameters, json_fields = get_parameters(request, action, view)

        field_input = request.query_params.get(self.fields_param, None)
        if field_input:
            fields    = self.get_fields(view, request, action)
            not_found = []

            for field in self._get_request_fields(facade, field_input):
                field = field.strip()

                if field == 'help':
                    return {
                        'detail': "API parameter '{}' help".format(self.fields_param),
                        'fields': fields
                    }

                if not re.match(r'^\(.+\)$', field):
                    if ':' in field:
                        function_components = field.split('(')
                        match_field = function_components[0]
                    else:
                        match_field = field

                    if '=' in match_field:
                        match_field = match_field.split('=')[1]

                    if match_field not in fields and not check_json_field(json_fields, match_field):
                        not_found.append({
                            'field': field,
                            'similar': rank_similar(fields.keys(), match_field, data = fields)
                        })

            if not_found:
                return {
                    'detail': "Requested fields for parameter '{}' not found".format(self.fields_param),
                    'not_found': not_found
                }
        return None


    def _get_request_fields(self, facade, fields = None):
        if fields:
            request_fields = []
            for field in fields.split(','):
                if field == 'atomic':
                    request_fields.extend(facade.atomic_fields)
                else:
                    request_fields.append(field)
        else:
            request_fields = facade.atomic_fields

        return request_fields


class OrderingFilterBackend(FieldValidationMixin, OrderingFilter):

    ordering_title = 'Ordering'
    ordering_description = 'Which fields to use when ordering the results (prefix with - (dash) for descending search)'


    def filter_queryset(self, request, queryset, view):
        ordering = self._get_request_fields(
            request.query_params.get(self.ordering_param, None)
        )

        if ordering:
            ordering = queryset.model.facade.parse_order(ordering)
            return annotated_query(queryset).order_by(*ordering)
        return queryset


    def get_schema_operation_parameters(self, view):
        return [
            {
                'name': self.ordering_param,
                'required': False,
                'in': 'query',
                'description': force_str(self.ordering_description),
                'schema': {
                    'type': 'csv<[(][-]string[)]>'
                }
            }
        ]

    def check_parameter_errors(self, view, request, action, facade):
        parameters, json_fields = get_parameters(request, action, view)

        ordering_input = request.query_params.get(self.ordering_param, None)
        if ordering_input:
            fields    = self.get_fields(view, request, action)
            not_found = []

            for field in self._get_request_fields(ordering_input):
                field = field.strip().removeprefix('-')

                if field == 'help':
                    return {
                        'detail': "API parameter '{}' help".format(self.ordering_param),
                        'fields': fields
                    }

                if not re.match(r'^\(.+\)$', field) and field not in fields and not check_json_field(json_fields, field):
                    not_found.append({
                        'field': field,
                        'similar': rank_similar(fields.keys(), field, data = fields)
                    })

            if not_found:
                return {
                    'detail': "Requested fields for parameter '{}' not found".format(self.ordering_param),
                    'not_found': not_found
                }
        return None


    def _get_request_fields(self, fields):
        if fields:
            return [ field.strip() for field in fields.split(',') ]
        return []


class LimitFilterBackend(FilterValidationMixin, BaseFilterBackend):

    limit_param = settings.LIMIT_PARAM
    limit_title = 'Limit'
    limit_description = 'Maximum number of results to return'


    def filter_queryset(self, request, queryset, view):
        limit = request.query_params.get(self.limit_param, None)
        if limit:
            queryset = queryset[:int(limit)]

        return queryset


    def get_schema_operation_parameters(self, view):
        return [
            {
                'name': self.limit_param,
                'required': False,
                'in': 'query',
                'description': force_str(self.limit_description),
                'schema': {
                    'type': 'number'
                }
            }
        ]

    def check_parameter_errors(self, view, request, action, facade):
        limit_input = request.query_params.get(self.limit_param, None)
        if limit_input is not None:
            try:
                limit = int(limit_input)
                if limit <= 0:
                    raise ValueError()

            except ValueError:
                return {
                    'detail': "{} parameter '{}' must be a positive integer greater than 0".format(self.limit_title, self.limit_param)
                }
        return None


class SearchFilterBackend(FilterValidationMixin, SearchFilter):

    search_title = 'Search'
    search_description = 'A search query ([ ^ ] startswith [ = ] exact match [ @ ] search [ $ ] regex)'


    def get_schema_operation_parameters(self, view):
        return [
            {
                'name': self.search_param,
                'required': False,
                'in': 'query',
                'description': force_str(self.search_description),
                'schema': {
                    'type': '[^=@$]string'
                }
            }
        ]

    def check_parameter_errors(self, view, request, action, facade):
        search_text_input = request.query_params.get(self.search_param, None)
        if search_text_input is not None and not search_text_input:
            return {
                'detail': "{} parameter '{}' can not be empty if specified".format(self.search_title, self.search_param)
            }
        return None


class CacheRefreshBackend(FilterValidationMixin, BaseFilterBackend):

    cache_param = settings.CACHE_PARAM
    cache_title = 'Cache Refresh'
    cache_description = 'Refresh page in cache'


    def filter_queryset(self, request, queryset, view):
        return queryset


    def get_schema_operation_parameters(self, view):
        # The functionality for this parameter is located in the system cache middleware
        return [
            {
                'name': self.cache_param,
                'required': False,
                'in': 'query',
                'description': force_str(self.cache_description),
                'schema': {
                    'type': 'bool'
                }
            }
        ]
