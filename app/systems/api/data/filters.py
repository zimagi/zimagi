from django.conf import settings
from django.utils.encoding import force_str
from rest_framework.settings import api_settings
from rest_framework.filters import BaseFilterBackend
from rest_framework_filters.filterset import FilterSet, FilterSetMetaclass
from rest_framework_filters.filters import BooleanFilter, NumberFilter, CharFilter, DateFilter, DateTimeFilter, RelatedFilter, BaseInFilter, BaseRangeFilter


FILTER_TYPES = ('bool', 'number', 'text', 'date', 'time')


def get_filter_parameters(request_params, expand_fields = True):
    parameters = []

    for parameter, value in request_params.items():
        if expand_fields and parameter in (settings.FIELDS_PARAM, api_settings.ORDERING_PARAM):
            parameters.extend([ field.strip().removeprefix('-') for field in value.split(',') ])
        else:
            parameters.append(parameter)

    return list(set(parameters))


class CharInFilter(BaseInFilter, CharFilter):
    pass

class CharRangeFilter(BaseRangeFilter, CharFilter):
    pass

class NumberInFilter(BaseInFilter, NumberFilter):
    pass

class NumberRangeFilter(BaseRangeFilter, NumberFilter):
    pass

class DateInFilter(BaseInFilter, DateFilter):
    pass

class DateRangeFilter(BaseRangeFilter, DateFilter):
    pass

class DateTimeInFilter(BaseInFilter, DateTimeFilter):
    pass

class DateTimeRangeFilter(BaseRangeFilter, DateTimeFilter):
    pass

class DataRelatedFilter(RelatedFilter):

    def get_queryset(self, request):
        return self.filterset._meta.model.objects.all()


class MetaFilterSet(FilterSetMetaclass):

    def __new__(cls, name, bases, attr):
        facade = attr.pop('_facade', None)
        related_fields = attr.get('related_fields', None)

        def _generate_filters(id):
            if id in attr and attr[id]:
                for field in list(attr[id]):
                    components = field.split(':')

                    if len(components) > 1:
                        info = {'name': components[0], 'field': components[1]}
                    else:
                        info = {'name': field, 'field': field}

                    getattr(cls, "{}_filters".format(id))(info, attr, facade)

            if id in attr.keys():
                attr.pop(id)

        _generate_filters('_boolean_fields')
        _generate_filters('_text_fields')
        _generate_filters('_number_fields')
        _generate_filters('_date_fields')
        _generate_filters('_time_fields')

        if related_fields:
            cls._generate_aggregator_fields(related_fields, attr, facade)

        return super().__new__(cls, name, bases, attr)


    @classmethod
    def _get_text_lookups(self):
        return ['iexact', 'contains', 'icontains', 'startswith', 'istartswith', 'endswith', 'iendswith', 'regex', 'iregex']

    @classmethod
    def _get_number_lookups(self):
        return ['lt', 'lte', 'gt', 'gte']

    @classmethod
    def _get_date_lookups(self):
        return ['year', 'month', 'day', 'week', 'week_day', 'quarter']

    @classmethod
    def _get_time_lookups(self):
        return self._get_date_lookups() + ['hour', 'minute', 'second']


    @classmethod
    def _boolean_fields_filters(cls, info, filters, facade):
        name = info['name']
        field = info['field']

        filters[name] = BooleanFilter(field_name = field, lookup_expr = 'exact')
        filters["{}__isnull".format(name)] = BooleanFilter(field_name = field, lookup_expr = 'isnull')


    @classmethod
    def _text_fields_filters(cls, info, filters, facade):
        name = info['name']
        field = info['field']

        filters[name] = CharFilter(field_name = field, lookup_expr = 'exact')
        filters["{}__isnull".format(name)] = BooleanFilter(field_name = field, lookup_expr = 'isnull')
        filters["{}__in".format(name)] = CharInFilter(field_name = field)

        for lookup in cls._get_text_lookups():
            filters['{}__{}'.format(name, lookup)] = CharFilter(field_name = field, lookup_expr = lookup)


    @classmethod
    def _number_fields_filters(cls, info, filters, facade):
        name = info['name']
        field = info['field']

        filters[name] = NumberFilter(field_name = field, lookup_expr = 'exact')
        filters["{}__isnull".format(name)] = BooleanFilter(field_name = field, lookup_expr = 'isnull')
        filters["{}__in".format(name)] = NumberInFilter(field_name = field)
        filters["{}__range".format(name)] = NumberRangeFilter(field_name = field)

        for lookup in cls._get_number_lookups():
            filters["{}__{}".format(name, lookup)] = NumberFilter(field_name = field, lookup_expr = lookup)


    @classmethod
    def _date_fields_filters(cls, info, filters, facade):
        name = info['name']
        field = info['field']

        filters[name] = CharFilter(field_name = field, lookup_expr = 'startswith')
        filters["{}__isnull".format(name)] = BooleanFilter(field_name = field, lookup_expr = 'isnull')
        filters["{}__date".format(name)] = DateFilter(field_name = field, lookup_expr = 'date')
        filters["{}__in".format(name)] = DateInFilter(field_name = field)
        filters["{}__range".format(name)] = DateRangeFilter(field_name = field)

        for lookup in cls._get_number_lookups():
            filters["{}__{}".format(name, lookup)] = DateFilter(field_name = field, lookup_expr = lookup)

        for lookup in cls._get_date_lookups():
            filters["{}__{}".format(name, lookup)] = NumberFilter(field_name = field, lookup_expr = lookup)
            filters["{}__{}__in".format(name, lookup)] = NumberInFilter(field_name = field)
            filters["{}__{}__range".format(name, lookup)] = NumberRangeFilter(field_name = field)

            for sub_lookup in cls._get_number_lookups():
                full_lookup = "{}__{}".format(lookup, sub_lookup)
                filters["{}__{}".format(name, full_lookup)] = NumberFilter(field_name = field, lookup_expr = full_lookup)


    @classmethod
    def _time_fields_filters(cls, info, filters, facade):
        name = info['name']
        field = info['field']

        filters[name] = CharFilter(field_name = field, lookup_expr = 'startswith')
        filters["{}__isnull".format(name)] = BooleanFilter(field_name = field, lookup_expr = 'isnull')
        filters["{}__time".format(name)] = DateTimeFilter(field_name = field, lookup_expr = 'time')
        filters["{}__in".format(name)] = DateTimeInFilter(field_name = field)
        filters["{}__range".format(name)] = DateTimeRangeFilter(field_name = field)

        for lookup in cls._get_number_lookups():
            filters["{}__{}".format(name, lookup)] = DateTimeFilter(field_name = field, lookup_expr = lookup)

        for lookup in cls._get_time_lookups():
            filters["{}__{}".format(name, lookup)] = NumberFilter(field_name = field, lookup_expr = lookup)
            filters["{}__{}__in".format(name, lookup)] = NumberInFilter(field_name = field)
            filters["{}__{}__range".format(name, lookup)] = NumberRangeFilter(field_name = field)

            for sub_lookup in cls._get_number_lookups():
                full_lookup = "{}__{}".format(lookup, sub_lookup)
                filters["{}__{}".format(name, full_lookup)] = NumberFilter(field_name = field, lookup_expr = full_lookup)


    @classmethod
    def _generate_aggregator_fields(cls, fields, filters, facade):

        def add_filters(field_name, aggregator_func):
            aggregator_field = "{}:{}".format(field_name, aggregator_func)
            filters[aggregator_field] = NumberFilter(field_name = aggregator_field, lookup_expr = 'exact')
            for lookup in cls._get_number_lookups():
                filters["{}__{}".format(aggregator_field, lookup)] = NumberFilter(field_name = aggregator_field, lookup_expr = lookup)

        for field, info in fields.items():
            related_facade = info['model'].facade

            for type in FILTER_TYPES:
                type_fields = getattr(related_facade, "{}_fields".format(type))

                if type_fields:
                    aggregators = related_facade.get_aggregators(type)

                    for field_name in type_fields:
                        for aggregator_func in aggregators:
                            add_filters("{}__{}".format(field, field_name), aggregator_func)


class BaseFilterSet(FilterSet, metaclass = MetaFilterSet):

    def __init__(self, data = None, queryset = None, relationship = None, **kwargs):
        super().__init__(
            data = data,
            queryset = queryset,
            relationship = relationship,
            **kwargs
        )
        parameters = get_filter_parameters(self.request.query_params, True)
        annotations = {}

        for field, info in self.related_fields.items():
            related_facade = info['model'].facade
            aggregator_map = related_facade.aggregator_map

            for type in FILTER_TYPES:
                type_fields = getattr(related_facade, "{}_fields".format(type))

                if type_fields:
                    aggregators = related_facade.get_aggregators(type)

                    for field_name in type_fields:
                        for aggregator_func in aggregators:
                            full_field_name = "{}__{}".format(field, field_name)
                            annotation_name = "{}:{}".format(full_field_name, aggregator_func)
                            aggregator_info = aggregator_map[aggregator_func]
                            include = False

                            for parameter in parameters:
                                if annotation_name in parameter:
                                    include = True

                            if include:
                                if aggregator_info['distinct']:
                                    annotations[annotation_name] = aggregator_info['class'](full_field_name, distinct = True)
                                else:
                                    annotations[annotation_name] = aggregator_info['class'](full_field_name)
        if annotations:
            self.queryset = self.queryset.annotate(**annotations)


def DataFilterSet(facade):
    class_name = "{}DataFilterSet".format(facade.name.title())

    if class_name in globals():
        return globals()[class_name]

    field_map = {
        '_facade': facade,
        '_boolean_fields': facade.bool_fields,
        '_text_fields': facade.text_fields,
        '_number_fields': facade.number_fields,
        '_date_fields': facade.date_fields,
        '_time_fields': facade.time_fields,
        'Meta': type('Meta', (object,), {
            'model': facade.model,
            'fields': []
        })
    }
    related_fields = {}

    for field_name, info in facade.get_referenced_relations().items():
        if getattr(info['model'], 'facade', None):
            relation_facade = info['model'].facade
            field_map[field_name] = DataRelatedFilter(
                "systems.api.data.filters.{}DataFilterSet".format(relation_facade.name.title())
            )
            if info['multiple']:
                related_fields[field_name] = info

    field_map['related_fields'] = related_fields

    filterset = type(class_name, (BaseFilterSet,), field_map)
    globals()[class_name] = filterset
    return filterset



class FieldSelectFilterBackend(BaseFilterBackend):
    fields_param = settings.FIELDS_PARAM
    fields_title = 'Fields'
    fields_description = 'Comma separated list of fields to return'


    def filter_queryset(self, request, queryset, view):
        request_fields = self._get_request_fields(
            queryset.model.facade,
            request.query_params.get(self.fields_param, None)
        )
        return queryset.values(*request_fields)

    def get_schema_operation_parameters(self, view):
        return [
            {
                'name': self.fields_param,
                'required': False,
                'in': 'query',
                'description': force_str(self.fields_description),
                'schema': {
                    'type': 'string',
                },
            },
        ]


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



class LimitFilterBackend(BaseFilterBackend):
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
                    'type': 'string',
                },
            },
        ]
