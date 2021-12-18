from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import exceptions
from rest_framework.schemas.openapi import SchemaGenerator, AutoSchema
from rest_framework_filters.backends import RestFrameworkFilterBackend


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
                    'text/plain': {
                        'schema': {}
                    }
                },
                'description': 'Status message'
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
                "retrieve",
                "list",
                "meta",
                "values",
                "count",
                "csv",
                "json"
            ]
        return method.lower() in ["get"]


    def get_filter_parameters(self, path, method):
        if not self.allows_filters(path, method):
            return []

        def load_parameters(view, name_prefix = '', depth = 1):
            relations = view.facade.get_referenced_relations()
            reverse_relations = view.facade.get_reverse_relations()
            parameters = []
            id_map = {}

            for filter_backend in view.get_filter_classes():
                if depth == 1 or filter_backend == RestFrameworkFilterBackend:
                    for parameter in filter_backend().get_schema_operation_parameters(view):
                        field_name = parameter['name']
                        nested_name = "{}__{}".format(name_prefix, field_name) if name_prefix else field_name

                        if field_name not in id_map:
                            if field_name in relations:
                                if depth < 3:
                                    related_view = relations[field_name]['model'].facade.get_viewset()(
                                        action = self.view.action
                                    )
                                    parameters.extend(load_parameters(
                                        related_view,
                                        nested_name,
                                        (depth + 1)
                                    ))
                            elif field_name not in reverse_relations:
                                parameter['name'] = nested_name
                                parameters.append(parameter)

                            id_map[field_name] = True

            return parameters

        return load_parameters(self.view)


    def get_responses(self, path, method):
        if self.view.action == 'csv':
            return get_csv_response_schema('CSV download of field data')
        else:
            responses = super().get_responses(path, method)

            if self.view.action in ('meta', 'json'):
                for status_code, response in responses.items():
                    for format, info in response['content'].items():
                        response['content'][format]['schema'] = {
                            'type': 'array',
                            'items': info['schema'] if self.view.action == 'meta' else {}
                        }
            return responses
