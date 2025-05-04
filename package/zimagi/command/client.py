import re

from .. import client
from .. import codecs as shared_codecs
from .. import exceptions, settings, utility
from . import codecs, schema, transports


class Client(client.BaseAPIClient):
    def __init__(
        self,
        port=settings.DEFAULT_COMMAND_PORT,
        verify_cert=settings.DEFAULT_VERIFY_CERT,
        options_callback=None,
        message_callback=None,
        init_commands=True,
        **kwargs,
    ):
        super().__init__(
            port=port,
            decoders=[
                codecs.ZimagiJSONCodec(),  # application/vnd.zimagi+json
                shared_codecs.JSONCodec(),  # application/json
            ],
            **kwargs,
        )
        self.transport = transports.CommandHTTPTransport(
            client=self, verify_cert=verify_cert, options_callback=options_callback, message_callback=message_callback
        )
        if not self.get_status().encryption:
            self.cipher = None

        self.schema = self.get_schema()
        self.init_commands = init_commands
        if self.init_commands:
            self._init_commands()

    def _init_commands(self):
        self.commands = {}
        self.actions = {}

        def collect_commands(command_info, parents):
            for command_name, info in command_info.items():
                api_path = "/".join(parents + [command_name])
                if isinstance(info, (schema.Router, schema.Action)):
                    self.commands[api_path] = info
                    if isinstance(info, schema.Action):
                        self.actions[api_path] = info
                else:
                    collect_commands(info, parents + [command_name])

        collect_commands(self.schema, [])

    def _normalize_path(self, command_name):
        return re.sub(r"(\s+|\.)", "/", command_name)

    def execute(self, command_name, **options):
        command_path = self._normalize_path(command_name)
        command = self._lookup(command_path)
        command_options = utility.format_options("POST", options)

        def validate(url, params):
            self._validate(command, params)

        def processor():
            return self._request("POST", command.url, command_options, validate_callback=validate)

        return utility.wrap_api_call("command", command_path, processor, command_options)

    def extend(self, remote, reference, provider=None, **fields):
        fields["reference"] = reference

        options = {"remote": remote, "module_fields": fields}
        if provider:
            options["module_provider_name"] = provider

        return self.execute("module/add", **options)

    def run_task(self, module_key, task_name, config=None, **options):
        return self.execute(
            "task", **{**options, "module_key": module_key, "task_key": task_name, "task_fields": config if config else {}}
        )

    def run_profile(self, module_key, profile_key, config=None, components=None, **options):
        return self.execute(
            "run",
            **{
                **options,
                "module_key": module_key,
                "profile_key": profile_key,
                "profile_config_fields": config if config else {},
                "profile_components": components if components else [],
            },
        )

    def destroy_profile(self, module_key, profile_key, config=None, components=None, **options):
        return self.execute(
            "destroy",
            **{
                **options,
                "module_key": module_key,
                "profile_key": profile_key,
                "profile_config_fields": config if config else {},
                "profile_components": components if components else [],
            },
        )

    def run_imports(self, names=None, tags=None, **options):
        return self.execute("import", **{**options, "import_names": names if names else [], "tags": tags if tags else []})

    def run_calculations(self, names=None, tags=None, **options):
        return self.execute(
            "calculate", **{**options, "calculation_names": names if names else [], "tags": tags if tags else []}
        )

    def _lookup(self, command_name):
        node = self.schema
        found = True

        for key in command_name.split("/"):
            try:
                node = node[key]
            except (KeyError, IndexError, TypeError):
                found = False

        if not found or not isinstance(node, schema.Action):
            if not self.init_commands:
                self._init_commands()

            related_actions = []
            for other_action in self.actions:
                if command_name in other_action:
                    related_actions.append(other_action)

            raise exceptions.ParseError(
                "Command {} does not exist.  Try one of: {}".format(command_name, ", ".join(related_actions))
            )
        return node

    def _validate(self, command, options):
        provided = set(options.keys())
        required = {field.name for field in command.fields if field.required}
        optional = {field.name for field in command.fields if not field.required}
        errors = {}

        missing = required - provided
        for item in missing:
            errors[item] = "Parameter is required"

        unexpected = provided - (optional | required)
        for item in unexpected:
            errors[item] = "Unknown parameter"

        if errors:
            raise exceptions.ParseError(errors)
