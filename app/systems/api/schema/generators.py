from rest_framework.schemas import coreapi, openapi


class CommandSchemaGenerator(coreapi.SchemaGenerator):

    def has_view_permissions(self, path, method, view):
        # Allow for one size fits all schema for caching purposes
        return True


    def get_keys(self, subpath, method, view):
        return [
            component for component
            in subpath.strip('/').split('/')
            if '{' not in component
        ]


class DataSchemaGenerator(openapi.SchemaGenerator):

    def has_view_permissions(self, path, method, view):
        # Allow for one size fits all schema for caching purposes
        return True

