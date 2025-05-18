import urllib

from rest_framework.schemas.generators import BaseSchemaGenerator
from rest_framework.schemas.inspectors import ViewInspector
from systems.api.command.views import Command
from systems.commands import help, schema


class SchemaError(Exception):
    pass


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
        command_index = {}
        descriptions = help.CommandDescriptions()

        def parse_parent_commands(command):
            if not command:
                return
            command_index[command.get_full_name()] = command
            parse_parent_commands(command.parent_instance)

        def insert_action(target, keys, action_schema, action_command):
            router = []

            parse_parent_commands(action_command)

            for key in keys[:-1]:
                router.append(key)

                if key not in target:
                    full_name = " ".join(router)
                    command = command_index.get(full_name, None)
                    if command is None:
                        raise SchemaError(f"Command {full_name} does not exist in action hierarchy")

                    target[key] = schema.Router(
                        name=full_name,
                        overview=command.get_description(True),
                        description=command.get_description(False),
                        epilog=command.get_epilog(),
                        priority=command.get_priority(),
                        resource=command.spec.get("resource", None),
                    )
                target = target[key]

            target[keys[-1]] = action_schema

        paths, view_endpoints = self._get_paths_and_endpoints(request)
        if not paths:
            return None

        prefix = self._determine_path_prefix(paths)

        for path, method, view in view_endpoints:
            if path != "/status/" and not path.startswith("/agent/"):
                if not self.has_view_permissions(path, method, view):
                    continue

                resource = view.get_resource() if isinstance(view, Command) else None
                keys = [component for component in path[len(prefix) :].strip("/").split("/")]

                insert_action(
                    commands,
                    keys,
                    view.schema.get_action(path, base_url=self.url, resource=resource),
                    getattr(view, "command", None),
                )

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


class CommandSchema(ViewInspector):

    def __init__(self, name="", overview="", description="", epilog="", priority=1, confirm=None, fields=None):
        super().__init__()
        self._name = name
        self._overview = overview
        self._description = description
        self._epilog = epilog
        self._priority = priority
        self._confirm = confirm
        self._fields = fields
        self._field_map = {}

    def get_action(self, path, base_url, resource):
        if base_url and path.startswith("/"):
            path = path[1:]

        return schema.Action(
            url=urllib.parse.urljoin(base_url, path),
            name=self._name,
            overview=self._overview,
            description=self._description,
            epilog=self._epilog,
            priority=self._priority,
            resource=resource,
            confirm=self._confirm,
            fields=self._fields,
        )

    def get_fields(self):
        if not self._field_map:
            for field in self._fields:
                self._field_map[field.name] = field
        return self._field_map
