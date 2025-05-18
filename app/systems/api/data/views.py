import logging
import traceback
from functools import lru_cache

import pandas
from django.core.exceptions import FieldError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from systems.api.views import wrap_api_call
from systems.commands import action
from systems.encryption.cipher import Cipher
from utility.data import rank_similar
from utility.query import get_field_values

from . import filters, pagination, renderers, schema, serializers
from .filter.backends import (
    CacheRefreshBackend,
    CompoundFilterBackend,
    FieldSelectFilterBackend,
    LimitFilterBackend,
    OrderingFilterBackend,
    RelatedFilterBackend,
    SearchFilterBackend,
)
from .response import EncryptedResponse

logger = logging.getLogger(__name__)


class PathSchema(APIView):
    schema = schema.PathSchema()
    renderer_classes = [
        renderers.DataSchemaJSONRenderer,
    ]

    def get(self, request, path, format=None):
        type = "schema"

        def processor():
            generator = schema.DataSchemaGenerator()
            operations, data, components = generator.get_path_info(search_path=path, request=request, full=True)
            if not operations:
                response = Response(
                    data={"detail": f"Requested path {path} could not be found"}, status=status.HTTP_404_NOT_FOUND
                )
            else:
                operations["x-components"] = components
                operations["x-data"] = data
                operations["x-parent"] = {"$ref": request.build_absolute_uri("/")}
                response = Response(operations)
            return response

        return wrap_api_call(type, request, processor, api_type="data_api", show_error=True)


class DataSet(APIView):
    schema = schema.DataSetSchema()

    def get(self, request, name, format=None):
        type = "dataset"

        def processor():
            command = action.primary(f"api dataset {type}", user=request.user)
            facade = command.facade(type, False)

            if name == "help":
                return EncryptedResponse(
                    data={"detail": "Datasets available", "datasets": get_field_values(facade.all(), facade.key())},
                    status=status.HTTP_501_NOT_IMPLEMENTED,
                    user=request.user.name if request.user else None,
                )

            dataset = facade.retrieve(name)
            if dataset:
                dataset.initialize(command)

                response = EncryptedResponse(
                    content_type="text/csv",
                    data=dataset.provider.load().to_csv(index=False),
                    user=request.user.name if request.user else None,
                )
                response["Content-Disposition"] = f'attachment; filename="zimagi-{name}-data.csv"'
            else:
                response = EncryptedResponse(
                    data={
                        "detail": "Requested dataset could not be found",
                        "similar": rank_similar(get_field_values(facade.all(), facade.key()), name, count=50),
                    },
                    status=status.HTTP_404_NOT_FOUND,
                    user=request.user.name if request.user else None,
                )
            return response

        return wrap_api_call(type, request, processor, api_type="data_api", show_error=True)


class BaseDataViewSet(ModelViewSet):
    facade = None

    lookup_value_regex = "[^/]+"
    action_filters = {
        "count": (SearchFilterBackend, CompoundFilterBackend, RelatedFilterBackend, CacheRefreshBackend),
        "list": (OrderingFilterBackend, "count"),
        "values": "list",
        "csv": (FieldSelectFilterBackend, LimitFilterBackend, "list"),
        "json": "csv",
    }
    filter_backends = []
    pagination_class = pagination.ResultSetPagination
    action_serializers = {}

    @lru_cache(maxsize=None)
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
        return Cipher.get("data_api", user=request.user.name if request.user else None)

    def decrypt_parameters(self, request):
        request.query_params._mutable = True

        cipher = self.get_cipher(request)
        for key, value in request.query_params.items():
            request.query_params[key] = cipher.decrypt(value) if value else None

        request.query_params._mutable = False

    def validate_parameters(self, facade, request, action):
        validation_errors = []

        for backend in self.get_filter_classes():
            error = backend().check_parameter_errors(self, request, action, facade)
            if error:
                validation_errors.append(error)

        if validation_errors:
            return EncryptedResponse(
                data=validation_errors if len(validation_errors) > 1 else validation_errors[0],
                status=status.HTTP_501_NOT_IMPLEMENTED,
                user=request.user.name if request.user else None,
            )
        return None

    def get_paginated_response(self, data, user=None):
        return self.paginator.get_paginated_response(data, user=user)

    def api_query(self, type, request, processor):
        self.decrypt_parameters(request)

        def outer_processor():
            queryset = self.get_queryset()
            validation_error = self.validate_parameters(queryset.model.facade, request, type)
            if validation_error:
                return validation_error

            try:
                return processor(self.filter_queryset(queryset))

            except FieldError as fe:
                logger.warning(f"<{request.user.name}> {request.path}: {fe}:\n\n{traceback.format_exc()}")
                return EncryptedResponse(
                    data={"detail": str(fe)},
                    status=status.HTTP_501_NOT_IMPLEMENTED,
                    user=request.user.name if request.user else None,
                )

        return wrap_api_call(type, request, outer_processor, api_type="data_api", show_error=True)

    def api_update(self, type, request, processor):
        self.decrypt_parameters(request)

        def outer_processor():
            try:
                return processor()

            except ValidationError as ve:
                return EncryptedResponse(
                    data={"detail": ve.get_full_details()},
                    status=status.HTTP_501_NOT_IMPLEMENTED,
                    user=request.user.name if request.user else None,
                )

        return wrap_api_call(type, request, outer_processor, api_type="data_api", show_error=True)

    def list(self, request, *args, **kwargs):
        def processor(queryset):
            command = action.primary("api list", user=request.user)
            page = self.paginate_queryset(queryset)

            if page is not None:
                return self.get_paginated_response(
                    self.get_serializer(page, many=True, command=command).data,
                    user=request.user.name if request.user else None,
                )

            return EncryptedResponse(
                data=self.get_serializer(queryset, many=True).data, user=request.user.name if request.user else None
            )

        return self.api_query("list", request, processor)

    def retrieve(self, request, *args, **kwargs):
        self.decrypt_parameters(request)

        def processor():
            try:
                command = action.primary("api get", user=request.user)
                return EncryptedResponse(
                    data=self.get_serializer(self.get_object(), command=command).data,
                    user=request.user.name if request.user else None,
                )
            except Exception as error:
                logger.warning(f"<{request.user.name}> {request.path}: {error}:\n\n{traceback.format_exc()}")
                return EncryptedResponse(
                    data={"detail": str(error)},
                    status=getattr(error, "status", status.HTTP_500_INTERNAL_SERVER_ERROR),
                    user=request.user.name if request.user else None,
                )

        return wrap_api_call("retrieve", request, processor, api_type="data_api", show_error=True)

    def values(self, request, *args, **kwargs):
        def processor(queryset):
            command = action.primary("api values", user=request.user)
            values = get_field_values(queryset, kwargs["field_lookup"])

            return EncryptedResponse(
                data=self.get_serializer(
                    {"count": len(values), "results": sorted(values)}, many=False, command=command
                ).data,
                user=request.user.name if request.user else None,
            )

        return self.api_query("values", request, processor)

    def count(self, request, *args, **kwargs):
        def processor(queryset):
            command = action.primary("api count", user=request.user)
            return EncryptedResponse(
                data=self.get_serializer(
                    {"count": len(get_field_values(queryset, kwargs["field_lookup"]))}, many=False, command=command
                ).data,
                user=request.user.name if request.user else None,
            )

        return self.api_query("count", request, processor)

    def csv(self, request, *args, **kwargs):
        def processor(queryset):
            response = EncryptedResponse(
                content_type="text/csv",
                data=pandas.DataFrame(list(queryset)).to_csv(index=False),
                user=request.user.name if request.user else None,
            )
            response["Content-Disposition"] = 'attachment; filename="zimagi-export-data.csv"'
            return response

        return self.api_query("csv", request, processor)

    def json(self, request, *args, **kwargs):
        def processor(queryset):
            return EncryptedResponse(data=list(queryset), user=request.user.name if request.user else None)

        return self.api_query("json", request, processor)

    def create(self, request, *args, **kwargs):
        def processor():
            command = action.primary(
                "api create", {"type": self.facade.name, "data": request.data}, user=request.user, log=True
            )
            success = True
            try:
                serializer = self.get_serializer(data=request.data, command=command)
                serializer.is_valid(raise_exception=True)
                serializer.save()

            except Exception as e:
                command.error(e, terminate=False)
                success = False
                raise e
            finally:
                command.log_status(success)

            return EncryptedResponse(
                data=serializer.data,
                user=request.user.name,
                status=status.HTTP_201_CREATED,
                headers=self.get_success_headers(serializer.data),
            )

        return self.api_update("create", request, processor)

    def update(self, request, *args, **kwargs):
        def processor():
            instance = self.get_object()
            command = action.primary(
                "api update",
                {"id": getattr(instance, instance.facade.pk), "type": instance.facade.name, "data": request.data},
                user=request.user,
                log=True,
            )
            success = True
            try:
                serializer = self.get_serializer(instance, data=request.data, partial=True, command=command)
                serializer.is_valid(raise_exception=True)
                serializer.save()

                if getattr(instance, "_prefetched_objects_cache", None):
                    instance._prefetched_objects_cache = {}

            except Exception as e:
                command.error(e, terminate=False)
                success = False
                raise e
            finally:
                command.log_status(success)

            return EncryptedResponse(data=serializer.data, user=request.user.name)

        return self.api_update("update", request, processor)

    def destroy(self, request, *args, **kwargs):
        def processor():
            instance = self.get_object()
            command = action.primary(
                "api delete",
                {"id": getattr(instance, instance.facade.pk), "type": instance.facade.name},
                user=request.user,
                log=True,
            )
            success = True
            try:
                command.remove_instance(
                    instance.facade, getattr(instance, instance.facade.key()), scope=command.get_scope_filters(instance)
                )
            except Exception as e:
                command.error(e, terminate=False)
                success = False
                raise e
            finally:
                command.log_status(success)

            return EncryptedResponse(user=request.user.name, status=status.HTTP_204_NO_CONTENT)

        return self.api_update("destroy", request, processor)


def DataViewSet(facade):
    class_name = f"{facade.name.title()}DataViewSet"

    if class_name in globals():
        return globals()[class_name]

    ordering = facade.meta.ordering

    viewset = type(
        class_name,
        (BaseDataViewSet,),
        {
            "facade": facade,
            "queryset": facade.model.objects.all().distinct(),
            "base_entity": facade.name,
            "lookup_field": facade.pk,
            "filterset_class": filters.DataFilterSet(facade),
            "search_fields": facade.text_fields,
            "ordering_fields": "__all__",
            "ordering": ordering,
            "action_serializers": {
                "retrieve": serializers.DetailSerializer(facade),
                "list": serializers.SummarySerializer(facade),
                "values": serializers.ValuesSerializer,
                "count": serializers.CountSerializer,
                "csv": serializers.BaseSerializer,  # Dummy serializer to prevent errors
                "json": serializers.BaseSerializer,  # Dummy serializer to prevent errors
                "create": serializers.UpdateSerializer(facade),
                "update": serializers.UpdateSerializer(facade),
                "destroy": serializers.BaseSerializer,  # Dummy serializer to prevent errors
            },
        },
    )
    globals()[class_name] = viewset
    return viewset
