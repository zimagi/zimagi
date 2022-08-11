from collections import OrderedDict

from django.db.models import QuerySet
from django.db.models.constants import LOOKUP_SEP
from django.db.models.lookups import Transform
from django_filters import filterset, rest_framework

from . import filters

import copy


class RelatedFilterError(Exception):
    pass


def lookups_for_transform(transform):
    lookups = []

    for expr, lookup in transform.output_field.get_lookups().items():
        if issubclass(lookup, Transform):
            if type(transform) == lookup:
                continue

            sub_transform = lookup(transform)
            lookups += [
                LOOKUP_SEP.join([ expr, sub_expr ]) for sub_expr
                in lookups_for_transform(sub_transform)
            ]

        else:
            lookups.append(expr)

    return lookups


def related(filterset, filter_name):
    if not filterset.relationship:
        return filter_name
    return LOOKUP_SEP.join([ filterset.relationship, filter_name ])


class RelatedFilterSetMetaclass(filterset.FilterSetMetaclass):

    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)

        new_class.related_filters = OrderedDict([
            (name, filter) for name, filter in new_class.declared_filters.items()
            if isinstance(filter, filters.BaseRelatedFilter)
        ])

        for filter in new_class.related_filters.values():
            filter.bind_filterset(new_class)

        return new_class


class RelatedFilterSet(rest_framework.FilterSet, metaclass = RelatedFilterSetMetaclass):

    def __init__(self, data = None, queryset = None, *, relationship = None, negate = None, **kwargs):
        self.relationship = relationship
        self.negate       = negate or {}
        self.base_filters = self.get_filter_subset(data or {}, relationship)

        super().__init__(data, queryset, **kwargs)

        self.related_filtersets = self.get_related_filtersets()
        self.filters            = self.get_request_filters()


    def get_filter_subset(self, params, relationship = None):
        filter_names  = { self.get_param_filter_name(param, relationship) for param in params }
        filter_names  = { name for name in filter_names if name is not None }

        return OrderedDict(
            (key, value) for key, value in self.base_filters.items() if key in filter_names
        )

    def get_param_filter_name(self, param, relationship = None):
        if not param:
            return param

        if param[0] == '-':
            param = param[1:]
            self.negate[param] = True

        if param == relationship:
            return None

        prefix = "{}{}".format(relationship or '', LOOKUP_SEP)
        if relationship and param.startswith(prefix):
            param = param[len(prefix):]

        if param in self.base_filters:
            return param

        if param in self.base_filters:
            return param
        else:
            for name in sorted(self.related_filters, reverse = True):
                if param.startswith("{}{}".format(name, LOOKUP_SEP)):
                    return name
        return None


    def get_related_filtersets(self):
        related_filtersets = OrderedDict()

        for related_name in self.related_filters:
            if related_name not in self.filters:
                continue

            filter = self.filters[related_name]
            related_filtersets[related_name] = filter.filterset(
                data         = self.data,
                request      = self.request,
                queryset     = filter.get_queryset(self.request),
                relationship = related(self, related_name),
                negate       = self.negate
            )
        return related_filtersets

    def get_request_filters(self):
        requested_filters = OrderedDict()

        for filter_name, filter in self.filters.items():
            full_filter_name = related(self, filter_name)

            if self.negate.get(full_filter_name, False):
                filter_copy = copy.deepcopy(self.base_filters[filter_name])
                filter_copy.parent  = filter.parent
                filter_copy.model   = filter.model
                filter_copy.exclude = True
                filter = filter_copy

            requested_filters[filter_name] = filter

        return requested_filters


    @property
    def form(self):
        if not hasattr(self, "_form"):
            prefix = "{}{}".format(self.relationship, LOOKUP_SEP) if self.relationship else ''
            data   = {}
            Form   = self.get_form_class()

            if self.is_bound:
                for param, value in self.data.items():
                    param = param[1:] if param[0] == '-' else param
                    param = param.removeprefix(prefix)
                    data[param] = value

            self._form = Form(data)

        return self._form


    def filter_queryset(self, queryset):
        errors = []

        for name, value in self.form.cleaned_data.items():
            try:
                queryset = self.filters[name].filter(queryset, value)
                if not isinstance(queryset, QuerySet):
                    raise RelatedFilterError("Expected '{}.{}' to return a QuerySet, but got a {} instead.".format(
                        type(self).__name__,
                        name,
                        type(queryset).__name__
                    ))
            except filters.FilterValidationError as e:
                errors.append(str(e))

        if errors:
            raise filters.FilterValidationError("\n".join(errors))

        queryset = self.filter_related_filtersets(queryset)
        return queryset


    def filter_related_filtersets(self, queryset):
        for related_name, related_filterset in self.related_filtersets.items():
            prefix = "{}{}".format(related(self, related_name), LOOKUP_SEP)
            skip   = True

            for value in self.data:
                value = value[1:] if value[0] == '-' else value
                if value.startswith(prefix):
                    skip = False
            if skip:
                continue

            field_name    = self.filters[related_name].field_name
            field         = self.filters[related_name].field
            to_field_name = getattr(field, 'to_field_name', 'pk') or 'pk'
            lookup_expr   = LOOKUP_SEP.join([field_name, 'in'])

            subquery = related_filterset.qs.values(to_field_name)
            queryset = queryset.filter(**{ lookup_expr: subquery })

            if self.related_filters[related_name].distinct:
                queryset = queryset.distinct()

        return queryset
