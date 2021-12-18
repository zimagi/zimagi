from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import exceptions
from rest_framework.compat import coreapi
from rest_framework.schemas.coreapi import SchemaGenerator, ManualSchema, AutoSchema, distribute_links


class CommandSchemaGenerator(SchemaGenerator):

    def get_schema(self, request = None, public = False):
        self._initialise_endpoints()

        links = self.get_links(None if public else request)
        if not links.links:
           return None

        url = self.url
        if not url and request is not None:
            url = request.build_absolute_uri()

        distribute_links(links)
        return coreapi.Document(
            title = self.title,
            description = self.description,
            url = url,
            content = links
        )


    def get_keys(self, subpath, method, view):
        return [
            component for component
            in subpath.strip('/').split('/')
            if '{' not in component
        ]


class StatusSchema(AutoSchema):
    pass


class CommandSchema(ManualSchema):

    def __init__(self, fields, description = '', encoding = None):
        super().__init__(fields, description, encoding)
        self.field_map = {}


    def get_fields(self):
        if not self.field_map:
            for field in self._fields:
                self.field_map[field.name] = field
        return self.field_map
