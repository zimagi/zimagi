from collections import OrderedDict
from datetime import datetime, date
from urllib.parse import quote

from django.conf import settings
from django.core.management import call_command
from django.http import HttpResponse, StreamingHttpResponse, HttpResponseNotFound

from rest_framework import status
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from rest_framework_filters.backends import RestFrameworkFilterBackend

from systems.api import filters, pagination, serializers
from utility.encryption import Cipher
from utility.runtime import check_api_test

import sys
import json
import csv
import logging

logger = logging.getLogger(__name__)


class Status(APIView):

    def get(self, request, format = None):
        try:
            call_command('check')
            return Response(
                'System check successful',
                status.HTTP_200_OK
            )
        except Exception as e:
            logger.error("Status check error: {}".format(e))
            return Response(
                'System check failed',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class Command(APIView):

    name = None
    command = None


    @property
    def schema(self):
        return self.command.get_schema()


    def get_env(self):
        return self.command.get_env()

    def groups_allowed(self):
        return self.command.groups_allowed()


    def post(self, request, format = None):
        options = self._format_options(request.POST)
        command = self._get_command(options)

        response = StreamingHttpResponse(
            streaming_content = command.handle_api(options),
            content_type = 'application/json'
        )
        response['Cache-Control'] = 'no-cache'
        return response


    def _format_options(self, options):
        cipher = Cipher.get('params')

        def process_item(key, value):
            key = cipher.decrypt(key)
            value = cipher.decrypt(value)
            return (key, value)

        return self.command.format_fields(options, process_item)

    def _get_command(self, options):
        command = type(self.command)(
            self.command.name,
            self.command.parent_instance
        )
        command.bootstrap(options)
        command.parse_base()
        return command


class BaseDataViewSet(ModelViewSet):

    lookup_value_regex = '[^/]+'
    action_filters = {
        'list': (
            filters.BaseComplexFilterBackend,
            RestFrameworkFilterBackend,
            SearchFilter,
            OrderingFilter
        ),
        'values': 'list',
        'count': 'list',
        'meta': 'list',
        'csv': 'list'
    }
    filter_backends = []
    pagination_class = pagination.ResultSetPagination
    action_serializers = {}


    def meta(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        return Response(self.get_serializer(queryset, many = True).data)


    def csv(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        response = HttpResponse(content_type = 'text/csv')
        response['Content-Disposition'] = 'attachment; filename="zimagi-export-data.csv"'

        writer = csv.writer(response)
        fields = None

        def _get_fields(field_data, prefix = ''):
            field_names = []
            for key, value in field_data.items():
                if isinstance(value, dict):
                    field_names.extend(_get_fields(value, "{}:".format(key)))
                else:
                    field_names.append("{}{}".format(prefix, key))

            return field_names

        def _get_values(field_names, field_data):
            field_values = []

            def _access_value(data, names):
                if len(names) > 1:
                    return _access_value(data[names[0]], names[1:])
                return data[names[0]]

            for name in field_names:
                field_values.append(_access_value(field_data, name.split(':')))

            return field_values

        for record in queryset:
            serializer_data = self.get_serializer(record).data

            if fields is None:
                fields = _get_fields(serializer_data)
                writer.writerow(fields)

            writer.writerow(_get_values(fields, serializer_data))

        return response


    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except AssertionError as e:
            logger.error("List data error: {}".format(e))
            return Response({'count': -1, 'previous': None, 'next': None, 'results': []})


    def values(self, request, *args, **kwargs):
        field_lookup = kwargs['field_lookup']
        queryset = self.filter_queryset(self.get_queryset().order_by(field_lookup))
        values = []

        for value in queryset.values_list(field_lookup, flat = True):
            if value is not None:
                if isinstance(value, (datetime, date)):
                    value = value.isoformat()
                    if value.endswith('+00:00'):
                        value = value[:-6] + 'Z'

                values.append(value)

        serializer = self.get_serializer({
            'count': len(values),
            'results': values
        }, many = False)
        return Response(serializer.data)

    def count(self, request, *args, **kwargs):
        field_lookup = kwargs['field_lookup']
        queryset = self.filter_queryset(self.get_queryset().order_by(field_lookup))

        serializer = self.get_serializer({
            'count': queryset.values_list(field_lookup, flat = True).count()
        }, many = False)
        return Response(serializer.data)


    def get_filter_classes(self):
        try:
            filters = self.action_filters[self.action]

            if isinstance(filters, str):
                filters = self.action_filters[filters]

            return filters

        except (KeyError, AttributeError) as e:
            return []

    def filter_queryset(self, queryset):
        self.filter_backends = self.get_filter_classes()
        return super().filter_queryset(queryset)


    @property
    def paginator(self):
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            elif check_api_test(self.request):
                self._paginator = pagination.TestResultSetPagination()
            elif not self._allow_pagination(self.request):
                self._paginator = pagination.ResultNoPagination()
            else:
                self._paginator = self.pagination_class()

        return self._paginator

    def _allow_pagination(self, request = None):
        if request and 'page' in request.query_params and int(request.query_params['page']) == 0:
            return False
        return True


    def get_serializer_class(self):
        try:
            if check_api_test(self.request):
                if 'test' in self.action_serializers:
                    serializer = self.action_serializers['test']
                else:
                    raise AttributeError()
            else:
                serializer = self.action_serializers[self.action]

            if isinstance(serializer, str):
                serializer = self.action_serializers[serializer]

            return serializer

        except (KeyError, AttributeError) as e:
            return super().get_serializer_class()


def DataViewSet(facade):
    class_name = "{}DataViewSet".format(facade.name.title())

    if class_name in globals():
        return globals()[class_name]

    search_fields = []
    ordering_fields = []
    ordering = facade.meta.ordering

    if getattr(facade.meta, 'search_fields', None):
        search_fields = facade.meta.search_fields

    if getattr(facade.meta, 'ordering_fields', None):
        ordering_fields = facade.meta.ordering_fields

    viewset = type(class_name, (BaseDataViewSet,), {
        'queryset': facade.model.objects.all().distinct(),
        'base_entity': facade.name,
        'lookup_field': facade.pk,
        'filter_class': filters.DataFilterSet(facade),
        'search_fields': search_fields,
        'ordering_fields': ordering_fields,
        'ordering': ordering,
        'action_serializers': {
            'list': serializers.SummarySerializer(facade),
            'retrieve': serializers.DetailSerializer(facade),
            'meta': serializers.MetaSerializer(facade),
            'csv': serializers.CSVSerializer(facade),
            'values': serializers.ValuesSerializer,
            'count': serializers.CountSerializer,
            'test': serializers.TestSerializer(facade)
        }
    })
    globals()[class_name] = viewset
    return viewset
