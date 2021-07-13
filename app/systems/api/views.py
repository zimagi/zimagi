from collections import OrderedDict
from datetime import datetime, date
from urllib.parse import quote

from django.conf import settings
from django.core.management import call_command
from django.http import HttpResponse, StreamingHttpResponse, HttpResponseNotFound, JsonResponse

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

    def get_host(self):
        return self.command.get_host()


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

    facade = None

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
        'csv': 'list',
        'json': 'list'
    }
    filter_backends = []
    pagination_class = pagination.ResultSetPagination
    action_serializers = {}


    def get_queryset(self, request_fields = None, annotations = None):
        queryset = super().get_queryset()

        if request_fields:
            if annotations is None:
                annotations = get_aggregate_fields(queryset.model.facade, request_fields)
            queryset = queryset.annotate(**annotations).values(*request_fields)

        return queryset

    def limit_queryset(self, queryset, count = None):
        if count:
            queryset = queryset[:int(count)]
        return queryset


    def get_query_info(self, facade, request):
        count = request.query_params.get('count', None)
        request_fields = get_request_fields(
            facade,
            request.query_params.get('fields', None)
        )
        annotations = get_aggregate_fields(facade, request_fields)

        self.search_fields = request_fields
        self.ordering_fields = request_fields

        return {
            'queryset': self.limit_queryset(
                self.filter_queryset(self.get_queryset(request_fields, annotations), annotations.keys()),
                count
            ),
            'fields': request_fields,
            'count': count
        }


    def csv(self, request, *args, **kwargs):
        query = self.get_query_info(self.queryset.model.facade, request)

        response = HttpResponse(content_type = 'text/csv')
        response['Content-Disposition'] = 'attachment; filename="zimagi-export-data.csv"'
        writer = csv.writer(response)
        writer.writerow(query['fields'])

        for record in query['queryset']:
            csv_row = []
            for field in query['fields']:
                csv_row.append(record.get(field, None))

            writer.writerow(csv_row)

        return response

    def json(self, request, *args, **kwargs):
        query = self.get_query_info(self.queryset.model.facade, request)
        data = []

        for record in query['queryset']:
            json_record = {}
            for field in query['fields']:
                json_record[field] = record.get(field, None)

            data.append(json_record)

        return JsonResponse(data, safe = False)


    def meta(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        return Response(self.get_serializer(queryset, many = True).data)


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

    def filter_queryset(self, queryset, aggregate_fields = None):
        self.filter_class = filters.DataFilterSet(self.facade, aggregate_fields)
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


def get_request_fields(facade, query_fields = None):
    if query_fields:
        request_fields = []
        for field in query_fields.split(','):
            if field == 'atomic':
                request_fields.extend(facade.atomic_fields)
            else:
                request_fields.append(field)
    else:
        request_fields = facade.atomic_fields

    return request_fields

def get_aggregate_fields(facade, request_fields):
    aggregate_fields = { type: [] for type in facade.aggregator_map.keys() }
    annotations = {}

    for field in request_fields:
        aggregated_field = False
        for type in aggregate_fields.keys():
            suffix = "_{}".format(type)
            if field.endswith(suffix):
                aggregate_fields[type].append(field[:-len(suffix)])
                aggregated_field = True

    for type, klass in facade.aggregator_map.items():
        if type in aggregate_fields:
            for field in aggregate_fields[type]:
                field_name = "{}_{}".format(field, type)
                if type == 'COUNT':
                    annotations[field_name] = klass(field, distinct = True)
                else:
                    annotations[field_name] = klass(field)

    return annotations


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
        'facade': facade,
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
            'csv': serializers.BaseSerializer, # Dummy serializer to prevent errors
            'json': serializers.BaseSerializer, # Dummy serializer to prevent errors
            'values': serializers.ValuesSerializer,
            'count': serializers.CountSerializer,
            'test': serializers.TestSerializer(facade)
        }
    })
    globals()[class_name] = viewset
    return viewset
