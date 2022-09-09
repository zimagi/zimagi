from functools import lru_cache

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import exceptions
from rest_framework.schemas.openapi import SchemaGenerator, AutoSchema

from .filter.backends import RelatedFilterBackend


def get_csv_response_schema(description):
    return {
        '200': {
            'content': {
                'text/csv': {
                    'schema': {}
                }
            },
            'description': description
        }
    }


class DataSchemaGenerator(SchemaGenerator):

    def has_view_permissions(self, path, method, view):
        if view.request is None:
            return True
        try:
            view.check_permissions(view.request)
        except (exceptions.APIException, Http404, PermissionDenied):
            return False
        return True


class StatusSchema(AutoSchema):

    def get_operation_id_base(self, path, method, action):
        return 'SystemStatus'

    def get_responses(self, path, method):
        return {
            '200': {
                'content': {
                    'application/json': {
                        'schema': {}
                    }
                },
                'description': 'Status information'
            }
        }


class DataSetSchema(AutoSchema):

    def get_operation_id_base(self, path, method, action):
        return 'DataSetCSV'

    def get_responses(self, path, method):
        return get_csv_response_schema('CSV download of dataset data')


class DataSchema(AutoSchema):

    def allows_filters(self, path, method):
        if getattr(self.view, 'filter_backends', None) is None:
            return False

        if hasattr(self.view, 'action'):
            return self.view.action in [
                "list",
                "values",
                "count",
                "csv",
                "json",
                "retrieve",
                "create",
                "update",
                "destroy"
            ]
        return method.lower() in ["get", "put", "delete"]


    @lru_cache(maxsize = None)
    def get_filter_parameters(self, path, method, recursive = False):
        if not self.allows_filters(path, method):
            return []

        def check_filter_overlap(name_prefix, field_name):
            for component in field_name.split('__'):
                if component in name_prefix:
                    return True
            return False

        def load_parameters(view, name_prefix = '', depth = 1):
            relations = view.facade.get_all_relations()
            parameters = []
            id_map = {}

            for filter_backend in view.get_filter_classes():
                if depth == 1 or filter_backend == RelatedFilterBackend:
                    for parameter in filter_backend().get_schema_operation_parameters(view):
                        field_name = parameter['name']

                        if not check_filter_overlap(name_prefix, field_name):
                            nested_name = "{}__{}".format(name_prefix, field_name) if name_prefix else field_name

                            if field_name not in id_map:
                                if field_name in relations:
                                    if recursive and depth < 3:
                                        related_view = relations[field_name]['model'].facade.get_viewset()(
                                            action = self.view.action
                                        )
                                        parameters.extend(load_parameters(
                                            related_view,
                                            nested_name,
                                            (depth + 1)
                                        ))
                                else:
                                    parameter['name'] = nested_name

                                    if 'x-field' in parameter['schema']:
                                        parameter['schema']['x-field'] = "{}{}".format(
                                            "{}__".format(name_prefix) if name_prefix else '',
                                            parameter['schema']['x-field']
                                        )
                                    parameters.append(parameter)

                                id_map[field_name] = True
            return parameters

        return load_parameters(self.view)


    @lru_cache(maxsize = None)
    def get_responses(self, path, method):
        if self.view.action == 'csv':
            return get_csv_response_schema('CSV download of field data')
        else:
            responses = super().get_responses(path, method)

            if self.view.action in ('json',):
                for status_code, response in responses.items():
                    for format, info in response['content'].items():
                        response['content'][format]['schema'] = {
                            'type': 'array',
                            'items': {}
                        }
            return responses
