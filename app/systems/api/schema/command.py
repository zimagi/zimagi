
from django.utils.six.moves.urllib import parse as urlparse

from rest_framework.compat import coreapi
from rest_framework.schemas import ManualSchema


class CommandSchema(ManualSchema):

    def __init__(self, fields, description = '', encoding = None):
        super().__init__(fields, description, encoding)


    def get_link(self, path, method, base_url):
        if base_url and path.startswith('/'):
            path = path[1:]

        return coreapi.Link(
            url = urlparse.urljoin(base_url, path),
            action = method.lower(),
            encoding = self._encoding,
            fields = self._fields,
            description = self._description
        )
