from collections import OrderedDict
from datetime import datetime, date
from urllib.parse import quote

from django.conf import settings
from django.core.management import call_command
from django.http import StreamingHttpResponse

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from rest_framework_filters.backends import RestFrameworkFilterBackend

from systems.api import mixins, filters, pagination
from systems.api.auth import CommandPermission
from utility.encryption import Cipher

import sys
import json
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

    permission_classes = [
        IsAuthenticated,
        CommandPermission
    ]

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


class BaseModelViewSet(
    mixins.FilterViewSetMixin,
    mixins.PaginationViewSetMixin,
    mixins.SerializerViewSetMixin,
    ModelViewSet
):
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
        'export_json': 'list',
        'export_csv': 'list'
    }
    pagination_class = pagination.ResultSetPagination


    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except AssertionError as e:
            logger.error("List data error: {}".format(e))
            return Response({'count': 0, 'previous': None, 'next': None, 'results': []})

    def full_list(self):
        queryset = self.filter_queryset(self.get_queryset())
        return self.get_serializer(queryset, many = True).data

    def list_ids(self):
        ids = []
        for id in self.filter_queryset(self.get_queryset()).values_list(self.lookup_field, flat = True):
            ids.append(id)

        return ids


    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

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

        return Response(OrderedDict([
            ('count', len(values)),
            ('results', values)
        ]))

    def count(self, request, *args, **kwargs):
        field_lookup = kwargs['field_lookup']
        queryset = self.filter_queryset(self.get_queryset().order_by(field_lookup))
        return Response({'count': queryset.values_list(field_lookup, flat = True).count()})


    def export(self, request, group_by, viewsets):
        ids = self.list_ids()
        data_series = []

        if len(ids):
            self._request_filters(request, ids)

            for viewset_cls in viewsets:
                data_series.append(self._view_data(viewset_cls, request))

            return self._combine_data(data_series, group_by)
        else:
            raise AssertionError('Not found')


    def _request_filters(self, request, ids):
        request = request._request
        filters = ['({}__{}__in={})'.format(self.base_entity, self.lookup_field, ",".join(ids))]

        if not request.GET._mutable:
            request.GET._mutable = True

        request.GET['page'] = 0

        for name, value in request.GET.items():
            filters.append('({}={})'.format(name, value))

        request.GET['filters'] = quote("&".join(filters))


    def _view_data(self, viewset_cls, request, op = 'list'):
        return self._normalize_data(getattr(viewset_cls, 'as_view')({'get': op})(request._request))


    def _normalize_data(self, response):
        results = {}

        for record in response.data['results']:
            url = record.pop('api_url')
            date = record.pop('date')

            id = record.pop('id')
            related_id = record.pop(self.base_entity)[self.lookup_field]

            if related_id not in results:
                results[related_id] = {}

            results[related_id][date] = {}
            for field, value in record.items():
                results[related_id][date][field] = value

        return results

    def _combine_data(self, data_sets, group_by):
        results = OrderedDict()

        instruments = []
        dates = []

        # Find all shared instruments
        for index, data in enumerate(data_sets):
            set_instruments = data.keys()
            instruments = set_instruments if index == 0 else set(instruments).intersection(set_instruments)

        instruments = sorted(instruments)

        # Find all shared dates
        for index, data in enumerate(data_sets):
            for instrument in instruments:
                set_dates = data[instrument].keys()
                dates = set_dates if index == 0 else set(dates).intersection(set_dates)

        dates = sorted(dates)

        # Parse data
        for index, data in enumerate(data_sets):
            for instrument in instruments:
                if group_by == 'instrument':
                    if instrument not in results:
                        results[instrument] = OrderedDict()

                    for date in dates:
                        if date not in results[instrument]:
                            results[instrument][date] = {}

                        for field, value in data[instrument][date].items():
                            results[instrument][date][field] = value
                else:
                    for date in dates:
                        if date not in results:
                            results[date] = OrderedDict()

                        if instrument not in results[date]:
                            results[date][instrument] = {}

                        for field, value in data[instrument][date].items():
                            results[date][instrument][field] = value
        return results
