from rest_framework.schemas import AutoSchema


class DataSchema(AutoSchema):

    def get_filter_fields(self, path, method):
        if not self._allows_filters(path, method):
            return []

        fields = []
        for filter_backend in self.view.get_filter_classes():
            fields += filter_backend().get_schema_fields(self.view)

        return fields

    def _allows_filters(self, path, method):
        if getattr(self.view, 'filter_backends', None) is None:
            return False

        if hasattr(self.view, 'action'):
            return self.view.action in ["list", "retrieve", "update", "partial_update", "destroy", "meta"]

        return method.lower() in ["get", "put", "patch", "delete"]