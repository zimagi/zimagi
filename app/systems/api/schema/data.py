from rest_framework.schemas.coreapi import AutoSchema


class DataSchema(AutoSchema):

    def get_filter_fields(self, path, method):
        if not self._allows_filters(path, method):
            return []

        fields = []
        for filter_backend in self.view.get_filter_classes():
            fields += filter_backend().get_schema_fields(self.view)

        return fields
