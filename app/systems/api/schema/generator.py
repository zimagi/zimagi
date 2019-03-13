from rest_framework.schemas import generators


class CommandSchemaGenerator(generators.SchemaGenerator):

    def get_keys(self, subpath, method, view):
        return [
            component for component
            in subpath.strip('/').split('/')
            if '{' not in component
        ]
