
from urllib.parse import urljoin

from rest_framework.compat import coreapi
from rest_framework.schemas.coreapi import ManualSchema


class CommandSchema(ManualSchema):

    def __init__(self, fields, description = '', encoding = None):
        super().__init__(fields, description, encoding)
        self.field_map = {}


    def get_fields(self):
        if not self.field_map:
            for field in self._fields:
                self.field_map[field.name] = field
        return self.field_map

    def get_link(self, path, method, base_url):
        if base_url and path.startswith('/'):
            path = path[1:]

        return coreapi.Link(
            url = urljoin(base_url, path),
            action = method.lower(),
            encoding = self._encoding,
            fields = self._fields,
            description = self._description
        )
