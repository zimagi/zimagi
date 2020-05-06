from rest_framework.schemas.openapi import AutoSchema


class DataSchema(AutoSchema):

    def get_filter_fields(self, path, method):
        if not self._allows_filters(path, method):
            return []

        fields = []
        id_map = {}

        for filter_backend in self.view.get_filter_classes():
            for field in filter_backend().get_schema_fields(self.view):
                if field.name not in id_map:
                    fields.append(field)
                    id_map[field.name] = True

        return fields

    def _allows_filters(self, path, method):
        if getattr(self.view, 'filter_backends', None) is None:
            return False

        if hasattr(self.view, 'action'):
            return self.view.action in [
                "list",
                "values",
                "count",
                "retrieve",
                "update",
                "partial_update",
                "destroy",
                "meta",
                "test"
            ]
        return method.lower() in ["get", "put", "patch", "delete"]