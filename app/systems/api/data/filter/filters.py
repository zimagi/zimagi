import datetime
import re

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.utils.module_loading import import_string
from django_filters.constants import EMPTY_VALUES
from django_filters.rest_framework.filters import *  # noqa: F403
from utility.data import normalize_value

ALL_LOOKUPS = "__all__"


class FilterValidationError(Exception):
    pass


def annotated_query(queryset, fields=None):
    annotations = queryset.model.facade.get_annotations()
    if annotations:
        for name, value in annotations.items():
            try:
                if fields and name in fields:
                    queryset = queryset.annotate(**{name: value})
                else:
                    queryset = queryset.alias(**{name: value})

            except ValueError:
                # Already exists
                pass
    return queryset


class FilterError(Exception):
    pass


class BaseFilter(Filter):  # noqa: F405
    validation_class = forms.Field

    def filter(self, queryset, value):
        lookup = f"{self.field_name}__{self.lookup_expr}"

        if isinstance(value, str) and not re.match(r"^\(.+\)$", value.strip()):
            try:
                value = self.validation_field.clean(value)
            except ValidationError as e:
                raise FilterValidationError("Filter parameter '{}' malformed: {}".format(lookup, ", ".join(e)))

            filter_data = self.get_filter_data(lookup, value)
        else:
            filter_data = {lookup: value}

        if value in EMPTY_VALUES:
            return queryset

        if self.distinct:
            queryset = queryset.distinct()

        filters = queryset.model.facade.parse_filters(filter_data)
        return self.get_method(annotated_query(queryset))(filters)

    def get_filter_data(self, lookup, value):
        # Override in subclass if needed
        return {lookup: value}

    @property
    def validation_field(self):
        if not hasattr(self, "_validation_field"):
            self._validation_field = self.validation_class(label=self.label, **self.extra.copy())
            self.add_validators(self._validation_field.validators)
        return self._validation_field

    def add_validators(self, validators):
        # Override in subclass if needed
        pass


class BooleanFilter(BaseFilter):
    validation_class = forms.NullBooleanField


class NumberFilter(BaseFilter):
    validation_class = forms.DecimalField

    def add_validators(self, validators):
        validators.append(MaxValueValidator(1e50))


class CharFilter(BaseFilter):
    validation_class = forms.CharField


class DateTimeFilterMixin:
    def _get_datetime_filter(self, lookup, value, label, formats):
        time = None
        time_index = 0

        for index, format in enumerate(formats):
            try:
                time = datetime.datetime.strptime(value, format)
                value = datetime.datetime.fromtimestamp(time.timestamp(), tz=datetime.UTC)
                time_index = index
                break

            except ValueError:
                pass

        if not time:
            raise ValueError("{} data {} is not a supported format: {}".format(label, value, ",".join(formats)))

        if lookup[0] == "-":
            self.exclude = True
            lookup = lookup[1:]

        return {lookup: value.strftime(formats[time_index])}


class DateFilter(BaseFilter):
    validation_class = forms.DateField


class DateSearchFilter(DateTimeFilterMixin, CharFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lookup_expr = "startswith"

    def get_filter_data(self, lookup, value):
        return self._get_datetime_filter(lookup, value, "Date", ["%Y-%m-%d", "%Y-%m", "%Y"])


class DateTimeFilter(BaseFilter):
    validation_class = forms.DateTimeField


class DateTimeSearchFilter(DateTimeFilterMixin, CharFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lookup_expr = "startswith"

    def get_filter_data(self, lookup, value):
        return self._get_datetime_filter(
            lookup, value, "Date time", ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H", "%Y-%m-%d", "%Y-%m", "%Y"]
        )


class JSONFilter(BaseFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lookup_expr = None

    def get_filter_data(self, lookup, value):
        return {self.field_name: normalize_value(value)}


class BaseRelatedFilter:
    def __init__(self, filterset, *args, lookups=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.filterset = filterset
        self.lookups = lookups or []

    def bind_filterset(self, filterset):
        if not hasattr(self, "bound_filterset"):
            self.bound_filterset = filterset

    def filterset():
        def fget(self):
            if isinstance(self._filterset, str):
                try:
                    self._filterset = import_string(self._filterset)
                except ImportError:
                    path = ".".join([self.bound_filterset.__module__, self._filterset])
                    self._filterset = import_string(path)
            return self._filterset

        def fset(self, value):
            self._filterset = value

        return locals()

    filterset = property(**filterset())

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if queryset is None:
            raise FilterError(
                "Method .get_queryset() for related filter '{}.{}' must return a QuerySet".format(
                    self.parent.__class__.__name__, self.field_name
                )
            )
        return queryset


class RelatedFilter(BaseRelatedFilter, ModelChoiceFilter):  # noqa: F405
    pass
