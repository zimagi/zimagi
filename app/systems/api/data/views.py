from django.core.exceptions import FieldError
from rest_framework import status
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_filters.backends import RestFrameworkFilterBackend

from systems.encryption.cipher import Cipher
from systems.commands.action import ActionCommand
from systems.api.views import wrap_api_call
from .response import EncryptedResponse, EncryptedCSVResponse
from . import filters, pagination, serializers, schema
from utility.data import rank_similar
from utility.query import get_field_values

import pandas
import logging


logger = logging.getLogger(__name__)


class DataSet(APIView):

    schema = schema.DataSetSchema()


    def get(self, request, name, format = None):
        type = 'dataset'

        def processor():
            command = ActionCommand(type)
            command._user.set_active_user(request.user)

            facade = command.facade(type, False)
            dataset = facade.retrieve(name)

            if dataset:
                response = EncryptedCSVResponse(
                    content_type = 'text/csv',
                    user = request.user.name if request.user else None
                )
                response['Content-Disposition'] = 'attachment; filename="zimagi-{}-data.csv"'.format(name)

                dataset.initialize(command)
                dataset.provider.load().to_csv(path_or_buf = response)
            else:
                response = EncryptedResponse(
                    data = {
                        'detail': 'Requested dataset could not be found',
                        'similar': rank_similar(get_field_values(facade.all(), facade.key()), name)
                    },
                    status = status.HTTP_404_NOT_FOUND,
                    user = request.user.name if request.user else None
                )
            return response

        return wrap_api_call(type, request, processor, api_type = 'data_api')


class BaseDataViewSet(ModelViewSet):

    facade = None

    lookup_value_regex = '[^/]+'
    action_filters = {
        'list': (
            'count',
            OrderingFilter
        ),
        'meta': (
            'list',
            filters.LimitFilterBackend
        ),
        'values': 'count',
        'count': (
            SearchFilter,
            RestFrameworkFilterBackend
        ),
        'csv': (
            'meta',
            filters.FieldSelectFilterBackend
        ),
        'json': 'csv'
    }
    filter_backends = []
    pagination_class = pagination.ResultSetPagination
    action_serializers = {}


    def get_filter_classes(self):

        def get_filters(action):
            filters = self.action_filters[action]
            results = []

            if isinstance(filters, str):
                filters = get_filters(filters)

            for filter in filters:
                if isinstance(filter, str):
                    results.extend(get_filters(filter))
                else:
                    results.append(filter)

            return results

        try:
            return get_filters(self.action)

        except (KeyError, AttributeError) as e:
            return []


    def get_serializer_class(self):
        try:
            return self.action_serializers[self.action]

        except (KeyError, AttributeError) as e:
            return super().get_serializer_class()


    def filter_queryset(self, queryset):
        self.filter_class = filters.DataFilterSet(self.facade)
        self.filter_backends = self.get_filter_classes()
        return super().filter_queryset(queryset)


    def get_cipher(self, request):
        return Cipher.get('data_api',
            user = request.user.name if request.user else None
        )

    def decrypt_parameters(self, request):
        request.query_params._mutable = True

        cipher = self.get_cipher(request)
        for key, value in request.query_params.items():
            request.query_params[key] = cipher.decrypt(value)

        request.query_params._mutable = False


    def validate_parameters(self, request, action):
        parameter_schema = {}
        not_found = []

        for parameter_info in self.schema.get_filter_parameters(request.path, action):
            if parameter_info['in'] == 'query':
                parameter_schema[parameter_info['name']] = parameter_info['schema']['type']

        for parameter in filters.get_filter_parameters(request.query_params, action in ('json', 'csv')):
            if parameter not in parameter_schema:
                not_found.append({
                    'parameter': parameter,
                    'similar': rank_similar(parameter_schema.keys(), parameter, data = parameter_schema)
                })

        if not_found:
            return EncryptedResponse(
                data = {
                    'detail': 'Requested parameters are not supported',
                    'not_found': not_found,
                    'supported': parameter_schema
                },
                status = status.HTTP_501_NOT_IMPLEMENTED,
                user = request.user.name if request.user else None
            )
        return None


    def get_paginated_response(self, data, user = None):
        return self.paginator.get_paginated_response(data, user = user)


    def api_query(self, type, request, processor):
        self.decrypt_parameters(request)

        def outer_processor():
            validation_error = self.validate_parameters(request, type)
            if validation_error:
                return validation_error

            try:
                return processor(self.filter_queryset(self.get_queryset()))

            except FieldError as fe:
                return EncryptedResponse(
                    data = { 'detail': str(fe) },
                    status = status.HTTP_501_NOT_IMPLEMENTED,
                    user = request.user.name if request.user else None
                )
        return wrap_api_call(type, request, outer_processor, api_type = 'data_api')


    def meta(self, request, *args, **kwargs):

        def processor(queryset):
            return EncryptedResponse(
                data = self.get_serializer(queryset, many = True).data,
                user = request.user.name if request.user else None
            )
        return self.api_query('meta', request, processor)

    def list(self, request, *args, **kwargs):

        def processor(queryset):
            page = self.paginate_queryset(queryset)
            if page is not None:
                return self.get_paginated_response(
                    self.get_serializer(page, many = True).data,
                    user = request.user.name if request.user else None
                )
            return EncryptedResponse(
                data = self.get_serializer(queryset, many = True).data,
                user = request.user.name if request.user else None
            )
        return self.api_query('list', request, processor)


    def retrieve(self, request, *args, **kwargs):
        self.decrypt_parameters(request)

        try:
            return EncryptedResponse(
                data = self.get_serializer(self.get_object()).data,
                user = request.user.name if request.user else None
            )
        except Exception as error:
            return EncryptedResponse(
                data = { 'detail': str(error) },
                status = getattr(error, 'status', status.HTTP_500_INTERNAL_SERVER_ERROR),
                user = request.user.name if request.user else None
            )


    def values(self, request, *args, **kwargs):

        def processor(queryset):
            values = get_field_values(queryset, kwargs['field_lookup'])
            return EncryptedResponse(
                data = self.get_serializer({
                    'count': len(values),
                    'results': sorted(values)
                }, many = False).data,
                user = request.user.name if request.user else None
            )
        return self.api_query('values', request, processor)

    def count(self, request, *args, **kwargs):

        def processor(queryset):
            return EncryptedResponse(
                data = self.get_serializer({
                    'count': len(get_field_values(queryset, kwargs['field_lookup']))
                }, many = False).data,
                user = request.user.name if request.user else None
            )
        return self.api_query('count', request, processor)


    def csv(self, request, *args, **kwargs):

        def processor(queryset):
            response = EncryptedCSVResponse(
                content_type = 'text/csv',
                user = request.user.name if request.user else None
            )
            response['Content-Disposition'] = 'attachment; filename="zimagi-export-data.csv"'

            pandas.DataFrame(list(queryset)).to_csv(path_or_buf = response)
            return response

        return self.api_query('csv', request, processor)

    def json(self, request, *args, **kwargs):

        def processor(queryset):
            return EncryptedResponse(
                data = list(queryset),
                user = request.user.name if request.user else None
            )
        return self.api_query('json', request, processor)


def DataViewSet(facade):
    class_name = "{}DataViewSet".format(facade.name.title())

    if class_name in globals():
        return globals()[class_name]

    ordering = facade.meta.ordering

    viewset = type(class_name, (BaseDataViewSet,), {
        'facade': facade,
        'queryset': facade.model.objects.all().distinct(),
        'base_entity': facade.name,
        'lookup_field': facade.pk,
        'filter_class': filters.DataFilterSet(facade),
        'search_fields': facade.text_fields,
        'ordering_fields': '__all__',
        'ordering': ordering,
        'action_serializers': {
            'retrieve': serializers.DetailSerializer(facade),
            'list': serializers.SummarySerializer(facade),
            'meta': serializers.MetaSerializer(facade),
            'values': serializers.ValuesSerializer,
            'count': serializers.CountSerializer,
            'csv': serializers.BaseSerializer, # Dummy serializer to prevent errors
            'json': serializers.BaseSerializer # Dummy serializer to prevent errors
        }
    })
    globals()[class_name] = viewset
    return viewset
