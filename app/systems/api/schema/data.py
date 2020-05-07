from rest_framework.schemas.openapi import AutoSchema


class DataSchema(AutoSchema):

    def get_filter_parameters(self, path, method):
        if not self.allows_filters(path, method):
            return []

        parameters = []
        id_map = {}

        for filter_backend in self.view.get_filter_classes():
            for parameter in filter_backend().get_schema_fields(self.view):
                if parameter.name not in id_map:
                    parameters.append(parameter)
                    id_map[field.name] = True

        return parameters

    def allows_filters(self, path, method):
        if getattr(self.view, 'filter_backends', None) is None:
            return False

        if hasattr(self.view, 'action'):
            return self.view.action in [
                "list",
                "values",
                "count",
                "retrieve",
                "meta",
                "test"
            ]
        return method.lower() in ["get"]