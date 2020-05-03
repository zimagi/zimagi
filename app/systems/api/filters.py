from django.db.models.query import QuerySet

from rest_framework_filters.filterset import FilterSet, FilterSetMetaclass
from rest_framework_filters.filters import BooleanFilter, NumberFilter, CharFilter, DateFilter, DateTimeFilter, RelatedFilter, BaseInFilter, BaseRangeFilter
from rest_framework_filters.backends import ComplexFilterBackend


class CharInFilter(BaseInFilter, CharFilter):
    pass

class CharRangeFilter(BaseRangeFilter, CharFilter):
    pass

class NumberInFilter(BaseInFilter, NumberFilter):
    pass

class NumberRangeFilter(BaseRangeFilter, NumberFilter):
    pass


class BaseComplexFilterBackend(ComplexFilterBackend):
    operators = {
        '&': QuerySet.intersection,
        '|': QuerySet.union,
        '-': QuerySet.difference,
    }


class MetaFilterSet(FilterSetMetaclass):

    def __new__(cls, name, bases, attr):

        def _generate_filters(id):
            if id in attr and attr[id]:
                for field in list(attr[id]):
                    components = field.split(':')

                    if len(components) > 1:
                        info = {'name': components[0], 'field': components[1]}
                    else:
                        info = {'name': field, 'field': field}

                    getattr(cls, "{}_filters".format(id))(info, attr)

            if id in attr.keys():
                attr.pop(id)

        _generate_filters('_boolean')
        _generate_filters('_token_text')
        _generate_filters('_fuzzy_text')
        _generate_filters('_number_text')
        _generate_filters('_number')
        _generate_filters('_date_time')

        return super().__new__(cls, name, bases, attr)


    @classmethod
    def _boolean_filters(cls, info, filters):
        name = info['name']
        field = info['field']

        filters[name] = BooleanFilter(field_name = field, lookup_expr = 'exact')

    @classmethod
    def _token_text_filters(cls, info, filters):
        name = info['name']
        field = info['field']

        filters[name] = CharFilter(field_name = field, lookup_expr = 'exact')
        filters['{}__in'.format(name)] = CharInFilter(field_name = field)

        for lookup in ('iexact',):
            filters['{}__{}'.format(name, lookup)] = CharFilter(field_name = field, lookup_expr = lookup)

    @classmethod
    def _fuzzy_text_filters(cls, info, filters):
        name = info['name']
        field = info['field']

        filters[name] = CharFilter(field_name = field, lookup_expr = 'exact')
        filters['{}__in'.format(name)] = CharInFilter(field_name = field)

        for lookup in ('iexact', 'contains', 'icontains', 'startswith', 'istartswith', 'endswith', 'iendswith', 'regex', 'iregex'):
            filters['{}__{}'.format(name, lookup)] = CharFilter(field_name = field, lookup_expr = lookup)

    @classmethod
    def _number_filters(cls, info, filters):
        name = info['name']
        field = info['field']

        filters[name] = NumberFilter(field_name = field, lookup_expr = 'exact')
        filters['{}__range'.format(name)] = NumberRangeFilter(field_name = field)
        filters['{}__in'.format(name)] = NumberInFilter(field_name = field)

        for lookup in ('lt', 'lte', 'gt', 'gte'):
            filters['{}__{}'.format(name, lookup)] = NumberFilter(field_name = field, lookup_expr = lookup)

    @classmethod
    def _number_text_filters(cls, info, filters):
        name = info['name']
        field = info['field']

        filters[name] = CharFilter(field_name = field, lookup_expr = 'exact')
        filters['{}__range'.format(name)] = CharRangeFilter(field_name = field)
        filters['{}__in'.format(name)] = CharInFilter(field_name = field)

        for lookup in ('lt', 'lte', 'gt', 'gte'):
            filters['{}__{}'.format(name, lookup)] = CharFilter(field_name = field, lookup_expr = lookup)

    @classmethod
    def _date_time_filters(cls, info, filters):
        name = info['name']
        field = info['field']

        filters[name] = CharFilter(field_name = field, lookup_expr = 'startswith')

        for lookup in ('year', 'month', 'day', 'week', 'week_day', 'quarter'):
            filters['{}__{}'.format(name, lookup)] = NumberFilter(field_name = field, lookup_expr = lookup)


class BaseFilterSet(FilterSet, metaclass = MetaFilterSet):
    pass

class RelatedFilter(RelatedFilter):
    def get_queryset(self, request):
        return self.filterset.Meta.model.objects.all()


def DataFilterSet(facade):
    field_map = {
        '_boolean': facade.boolean_fields,
        '_token_text': facade.token_text_fields,
        '_fuzzy_text': facade.fuzzy_text_fields,
        '_number_text': facade.number_text_fields,
        '_number': facade.number_fields,
        '_date_time': facade.date_time_fields,
        'Meta': type('Meta', {
            'model': facade.model,
            'fields': []
        })
    }
    for field_name, info in facade.get_all_relations().items():
        if getattr(info['model'], 'facade', None):
            relation_facade = info['model'].facade
            field_map[field_name] = RelatedFilter(relation_facade.viewset.filter_class)

    return type('DataFilterSet', BaseFilterSet, field_map)