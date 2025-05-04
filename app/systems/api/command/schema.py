import urllib

from django.conf import settings
from rest_framework.schemas.generators import BaseSchemaGenerator
from rest_framework.schemas.inspectors import ViewInspector
from systems.api.command.views import Command
from systems.commands import help, schema


class CommandSchemaGenerator(BaseSchemaGenerator):
    def get_schema(self, request=None, public=False):
        self._initialise_endpoints()

        commands = self.get_commands(None if public else request)
        if not commands:
            return None

        url = self.url
        if not url and request is not None:
            url = request.build_absolute_uri()

        return schema.Root(commands, url=url, title=self.title, description=self.description)

    def get_commands(self, request=None):
        commands = schema.Router()
        descriptions = help.CommandDescriptions()

        def insert_action(target, keys, value):
            router = []
            for key in keys[:-1]:
                router.append(key)

                if key not in target:
                    full_name = " ".join(router)
                    spec = settings.MANAGER.get_spec("command." + ".".join(router))

                    target[key] = schema.Router(
                        name=full_name,
                        overview=descriptions.get(full_name, True),
                        description=descriptions.get(full_name, False),
                        priority=spec.get("priority", 1),
                        resource=spec.get("resource", None),
                    )
                target = target[key]

            target[keys[-1]] = value

        paths, view_endpoints = self._get_paths_and_endpoints(request)
        if not paths:
            return None

        prefix = self._determine_path_prefix(paths)

        for path, method, view in view_endpoints:
            if not self.has_view_permissions(path, method, view):
                continue

            resource = view.get_resource() if isinstance(view, Command) else None
            keys = [component for component in path[len(prefix) :].strip("/").split("/")]

            insert_action(commands, keys, view.schema.get_action(path, method, base_url=self.url, resource=resource))

        return commands

    def _determine_path_prefix(self, paths):
        prefixes = []
        for path in paths:
            components = path.strip("/").split("/")
            initial_components = []
            for component in components:
                initial_components.append(component)

            prefix = "/".join(initial_components[:-1])
            if not prefix:
                return "/"

            prefixes.append("/" + prefix + "/")
        return self._common_path(prefixes)

    def _common_path(self, paths):
        split_paths = [path.strip("/").split("/") for path in paths]
        s1 = min(split_paths)
        s2 = max(split_paths)

        common = s1
        for i, c in enumerate(s1):
            if c != s2[i]:
                common = s1[:i]
                break

        return "/" + "/".join(common)


class StatusSchema(ViewInspector):

    def __init__(self, encoding=None):
        super().__init__()
        self._encoding = encoding

    def get_action(self, path, method, base_url, resource):
        if base_url and path.startswith("/"):
            path = path[1:]

        return schema.Action(
            url=urllib.parse.urljoin(base_url, path),
            method=method.lower(),
            encoding=self._encoding,
        )


class CommandSchema(ViewInspector):

    def __init__(self, name="", overview="", description="", priority=1, encoding=None, fields=None):
        super().__init__()
        self._name = name
        self._overview = overview
        self._description = description
        self._priority = priority
        self._encoding = encoding
        self._fields = fields
        self._field_map = {}

    def get_action(self, path, method, base_url, resource):
        if base_url and path.startswith("/"):
            path = path[1:]

        return schema.Action(
            url=urllib.parse.urljoin(base_url, path),
            method=method.lower(),
            encoding=self._encoding,
            name=self._name,
            overview=self._overview,
            description=self._description,
            priority=self._priority,
            resource=resource,
            fields=self._fields,
        )

    def get_fields(self):
        if not self._field_map:
            for field in self._fields:
                self._field_map[field.name] = field
        return self._field_map
