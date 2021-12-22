from collections import Counter, OrderedDict
from rest_framework.schemas.generators import BaseSchemaGenerator
from rest_framework.schemas.inspectors import ViewInspector

from systems.commands.schema import Document, Object, Link

import urllib


class CommandSchemaGenerator(BaseSchemaGenerator):

    def get_schema(self, request = None, public = False):
        self._initialise_endpoints()

        links = self.get_links(None if public else request)
        if not links:
           return None

        url = self.url
        if not url and request is not None:
            url = request.build_absolute_uri()

        return Document(
            url = url,
            title = self.title,
            description = self.description,
            content = links
        )

    def get_links(self, request = None):
        links = Object()

        def insert_link(target, keys, value):
            for key in keys[:-1]:
                if key not in target:
                    target[key] = Object()
                target = target[key]

            target[keys[-1]] = value

        paths, view_endpoints = self._get_paths_and_endpoints(request)
        if not paths:
            return None

        prefix = self._determine_path_prefix(paths)

        for path, method, view in view_endpoints:
            if not self.has_view_permissions(path, method, view):
                continue

            keys = [
                component for component
                in path[len(prefix):].strip('/').split('/')
            ]
            insert_link(links, keys,
                view.schema.get_link(path, method, base_url = self.url)
            )
        return links


    def _determine_path_prefix(self, paths):
        prefixes = []
        for path in paths:
            components = path.strip('/').split('/')
            initial_components = []
            for component in components:
                initial_components.append(component)

            prefix = '/'.join(initial_components[:-1])
            if not prefix:
                return '/'

            prefixes.append('/' + prefix + '/')
        return self._common_path(prefixes)


    def _common_path(self, paths):
        split_paths = [ path.strip('/').split('/') for path in paths ]
        s1 = min(split_paths)
        s2 = max(split_paths)

        common = s1
        for i, c in enumerate(s1):
            if c != s2[i]:
                common = s1[:i]
                break

        return '/' + '/'.join(common)


class BaseSchema(ViewInspector):

    def __init__(self, fields = None, description = '', encoding = None):
        super().__init__()
        self._fields = fields
        self._description = description
        self._encoding = encoding

    def get_link(self, path, method, base_url):
        if base_url and path.startswith('/'):
            path = path[1:]

        return Link(
            url = urllib.parse.urljoin(base_url, path),
            action = method.lower(),
            encoding = self._encoding,
            fields = self._fields,
            description = self._description
        )


class StatusSchema(BaseSchema):
    pass


class CommandSchema(BaseSchema):

    def __init__(self, fields, description = '', encoding = None):
        super().__init__(fields, description, encoding)
        self.field_map = {}

    def get_fields(self):
        if not self.field_map:
            for field in self._fields:
                self.field_map[field.name] = field
        return self.field_map
