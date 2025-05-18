import copy
import importlib
import logging
import re
import sys
import types

from django.conf import settings
from systems.commands.factory import resource
from systems.models import index as model_index
from utility.data import ensure_list
from utility.python import PythonParser
from utility.time import Time

logger = logging.getLogger(__name__)


class CommandNotExistsError(Exception):
    pass


class SpecNotFound(Exception):
    pass


class ParseMethodNotSupportedError(Exception):
    pass


class ParseError(Exception):
    pass


class CallbackNotExistsError(Exception):
    pass


def get_dynamic_class_name(class_name):
    if check_dynamic(class_name):
        return class_name
    return f"{class_name}Dynamic"


def check_dynamic(class_name):
    return class_name.endswith("Dynamic")


def get_stored_class_name(class_name):
    return re.sub(r"Dynamic$", "", class_name)


def get_command_name(key, name, spec=None):
    if key != "command" and spec and "class" in spec:
        return spec["class"]
    return "".join([component.title() for component in name.split(".")[-1].split("_")])


def get_module_name(key, name):
    if key == "command_base":
        module_path = f"commands.base.{name}"
    elif key == "command_mixins":
        module_path = f"commands.mixins.{name}"
    elif key == "command":
        module_path = f"commands.{name}"
    else:
        raise SpecNotFound(f"Key {key} is not supported for command: {name}")
    return module_path


def get_spec_key(module_name):
    if re.match(r"^commands.base.[^\.]+$", module_name):
        key = "command_base"
    elif re.match(r"^commands.mixins.[^\.]+$", module_name):
        key = "command_mixins"
    elif re.match(r"^commands.[a-z\_\.]+$", module_name):
        key = "command"
    else:
        raise SpecNotFound(f"Key for module {module_name} was not found for command")
    return key


def generate_command_tree(spec, name="root", parent_command=None, lookup_path=""):
    from systems.commands.router import RouterCommand

    command = RouterCommand(name, parent_command, spec.get("priority", 1))

    if name != "root":
        if "base" in spec:
            if "resource" in spec:
                _generate_resource_commands(command, name, spec)
            else:
                return Command(lookup_path)

    for sub_name, sub_spec in spec.items():
        if isinstance(sub_spec, dict):
            subcommand = generate_command_tree(sub_spec, sub_name, command, f"{lookup_path}.{sub_name}".strip("."))
            if subcommand:
                command[sub_name] = subcommand

    return command if not command.is_empty else None


def find_command(full_name, parent=None):
    from systems.commands.router import RouterCommand

    def find(components, command, parents=None):
        if not parents:
            parents = []

        name = components.pop(0)

        if isinstance(command, RouterCommand):
            subcommand = command.get(name)

            if command.name != "root":
                parents.append(command)

            if subcommand:
                if len(components):
                    command = find(components, subcommand, parents)
                else:
                    command = subcommand
            else:
                parent_names = [x.name for x in parents]
                command_name = "{} {}".format(" ".join(parent_names), name) if parent_names else name

                if parents:
                    command_parent = parents[-1]
                    command_parent.print()
                    command_parent.print_help()

                raise CommandNotExistsError(f"Command '{command_name}' not found", parent)

        if isinstance(command, RouterCommand):
            return command
        else:
            return type(command)(command.name, command.parent_instance)

    command_args = re.split(r"\s+", full_name) if isinstance(full_name, str) else list(full_name)
    command = find(copy.copy(command_args), settings.MANAGER.index.command_tree)
    if parent:
        command.exec_parent = parent

        if parent.parent_messages:
            command.parent_messages = parent.parent_messages
        else:
            command.parent_messages = parent.messages

    return command


class CommandGenerator:
    def __init__(self, key, name, **options):
        self.parser = PythonParser({"time": Time(), "settings": settings})
        self.key = key
        self.name = name

        self.full_spec = settings.MANAGER.get_spec()

        try:
            self.spec = self.full_spec[key]
            for name_component in name.split("."):
                self.spec = self.spec[name_component]
        except Exception as e:
            raise CommandNotExistsError(f"Command specification {key} {name} does not exist")

        self.spec = self.parse_values(self.spec)

        self.class_name = get_command_name(self.key, self.name, self.spec)
        self.dynamic_class_name = get_dynamic_class_name(self.class_name)

        if options.get("base_command", None):
            self.base_command = options["base_command"]
        else:
            if self.key == "command_base" and self.name == "agent":
                from systems.commands import agent

                self.base_command = agent.AgentCommand
            else:
                from systems.commands import action

                self.base_command = action.ActionCommand

        module_info = self.get_module(name)
        self.module = module_info["module"]
        self.module_path = module_info["path"]

        self.parents = []
        self.attributes = {}

    @property
    def klass(self):
        if getattr(self.module, self.class_name, None):
            klass = getattr(self.module, self.class_name)
        else:
            klass = getattr(self.module, self.dynamic_class_name, None)

        return klass

    def get_command(self, name, type_function, error=True):
        klass = self.parse_values(name)
        if isinstance(klass, str):
            try:
                klass = type_function(name)
            except CommandNotExistsError as e:
                if error:
                    raise e
                klass = None
        return klass

    def create_module(self, module_path):
        module = types.ModuleType(module_path)
        sys.modules[module_path] = module
        return module

    def get_module(self, name, key=None):
        if key is None:
            key = self.key

        module_path = get_module_name(key, name)
        try:
            module = importlib.import_module(module_path)
        except ModuleNotFoundError:
            module = self.create_module(module_path)

        return {"module": module, "path": module_path}

    def init(self, attributes=None):
        self.init_parents()
        self.init_default_attributes(attributes)

    def init_parents(self):
        if "base" not in self.spec:
            self.parents = [self.base_command]
        else:
            if self.key == "command_mixins":
                self.parents = [self.get_command(self.spec["base"], CommandMixin)]
            else:
                self.parents = [self.get_command(self.spec["base"], BaseCommand)]

        if "mixins" in self.spec:
            for mixin in ensure_list(self.spec["mixins"]):
                mixin_class = self.get_command(mixin, CommandMixin, error=False)
                if mixin_class is not None:
                    self.parents.append(mixin_class)

    def init_default_attributes(self, attributes):
        if attributes is None:
            attributes = {}
        self.attributes = attributes

    def attribute(self, name, value):
        self.attributes[name] = value

    def method(self, method, *spec_fields):
        if self._check_include(spec_fields):
            self.attributes[method.__name__] = method

    def _check_include(self, spec_fields):
        include = True
        if spec_fields:
            for field in spec_fields:
                if field not in self.spec:
                    include = False
        return include

    def create(self):
        parent_classes = copy.deepcopy(self.parents)
        parent_classes.reverse()

        command = type(self.dynamic_class_name, tuple(parent_classes), self.attributes)
        command.__module__ = self.module_path
        setattr(self.module, self.dynamic_class_name, command)

        for parent in self.parents:
            parent.generate(command, self)  # Allow parents to initialize class

        return command

    def parse_values(self, item):
        if isinstance(item, (list, tuple)):
            for index, element in enumerate(item):
                item[index] = self.parse_values(element)
        elif isinstance(item, dict):
            for name, element in item.items():
                item[name] = self.parse_values(element)
        elif isinstance(item, str):
            item = self.parser.parse(item)
        return item


def BaseCommand(name):
    return _Command("command_base", name)


def Command(lookup_path):
    return _Command("command", lookup_path)


def Agent(lookup_path):
    return _Command("command", "agent.{}".format(lookup_path.removeprefix("agent.")))


def CommandMixin(name):
    from systems.commands.mixins import base

    mixin = CommandGenerator("command_mixins", name, base_command=base.BaseMixin)
    klass = mixin.klass
    if klass:
        return klass

    if not mixin.spec:
        raise CommandNotExistsError(f"Command mixin {mixin.class_name} does not exist yet")

    return _create_command_mixin(mixin)


def _Command(key, name, **options):
    command = CommandGenerator(key, name, **options)
    klass = command.klass
    if klass:
        return klass

    if not command.spec:
        raise CommandNotExistsError(f"Command {command.class_name} does not exist yet")

    return _create_command(command)


def _get_command_methods(command):
    # BaseCommand method overrides

    def __str__(self):
        class_name = command.class_name
        if not getattr(command.module, command.class_name, None):
            class_name = command.dynamic_class_name
        return f"{class_name} <{command.name}>"

    def get_priority(self):
        return command.spec["priority"]

    def api_enabled(self):
        return command.spec["api_enabled"]

    def mcp_enabled(self):
        return command.spec["mcp_enabled"]

    def groups_allowed(self):
        if command.spec["groups_allowed"] is False:
            return False

        from settings.roles import Roles

        return [Roles.admin] + ensure_list(command.spec["groups_allowed"])

    if "parameters" in command.spec:
        for name, info in command.spec["parameters"].items():
            command.method(_get_parse_method(name, info))
            command.method(_get_check_method(name, info))
            command.attribute(name, _get_accessor_method(name, info))

    def require_db(self):
        return command.spec["require_db"]

    def bootstrap_ensure(self):
        return command.spec["bootstrap_ensure"]

    def interpolate_options(self):
        return command.spec["interpolate_options"]

    def parse_passthrough(self):
        return command.spec["parse_passthrough"]

    def parse(self, add_api_fields=False):
        if isinstance(command.spec["parse"], (str, list, tuple)):
            for name in ensure_list(command.spec["parse"]):
                if (
                    add_api_fields
                    or "parameters" not in command.spec
                    or name not in command.spec["parameters"]
                    or not (settings.CLI_EXEC and command.spec["parameters"][name].get("api_only", False))
                ):
                    getattr(self, f"parse_{name}")()

        elif isinstance(command.spec["parse"], dict):
            for name, options in command.spec["parse"].items():
                if (
                    add_api_fields
                    or "parameters" not in command.spec
                    or name not in command.spec["parameters"]
                    or not (settings.CLI_EXEC and command.spec["parameters"][name].get("api_only", False))
                ):
                    parse_method = getattr(self, f"parse_{name}")

                    if options is None:
                        parse_method()
                    elif isinstance(options, (bool, int, float, str, list, tuple)):
                        parse_method(*ensure_list(options))
                    elif isinstance(options, dict):
                        parse_method(**options)
                    else:
                        raise ParseError(
                            "Command parameter parse options {} not recognized: {}".format(options, command.spec["parse"])
                        )
        else:
            raise ParseError("Command parameter parse list not recognized: {}".format(command.spec["parse"]))

    def confirm(self):
        return command.spec["confirm"]

    # ExecCommand method overrides

    def display_header(self):
        return command.spec["display_header"]

    def get_run_background(self):
        return command.spec["background"]

    def get_worker_type(self):
        return command.spec["worker_type"]

    def get_task_retries(self):
        return command.spec["task_retries"]

    def get_task_priority(self):
        return command.spec["task_priority"]

    if command.key == "command":
        command.method(__str__)

    command.method(get_priority, "priority")
    command.method(api_enabled, "api_enabled")
    command.method(mcp_enabled, "mcp_enabled")
    command.method(groups_allowed, "groups_allowed")
    command.method(require_db, "require_db")
    command.method(bootstrap_ensure, "bootstrap_ensure")
    command.method(interpolate_options, "interpolate_options")
    command.method(parse_passthrough, "parse_passthrough")
    command.method(parse, "parse")
    command.method(confirm, "confirm")
    command.method(display_header, "display_header")
    command.method(get_run_background, "background")
    command.method(get_worker_type, "worker_type")
    command.method(get_task_retries, "task_retries")
    command.method(get_task_priority, "task_priority")


def _create_command(command):
    command.init()
    _get_command_methods(command)
    return command.create()


def _create_command_mixin(mixin):
    schema_info = {}

    if "meta" in mixin.spec:
        for name, info in mixin.spec["meta"].items():
            schema_info[name] = {}

            if "data" in info and info["data"] is not None:
                schema_info[name]["data"] = info["data"]
                schema_info[name]["model"] = model_index.Model(info["data"])
                schema_info[name]["relations"] = info.get("relations", False)

                if "name_default" in info:
                    schema_info[name]["name_default"] = info["name_default"]

                if "provider" in info:
                    schema_info[name]["provider"] = info["provider"]
                if "default" in info:
                    schema_info[name]["default"] = info["default"]

    mixin.init({"schema": schema_info})
    _get_command_methods(mixin)
    klass = mixin.create()

    def __init__(self, *args, **kwargs):
        super(klass, self).__init__(*args, **kwargs)

        for name, info in schema_info.items():
            if "model" in info and getattr(settings, "DB_LOCK", None):
                priority = 50
                if "priority" in mixin.spec["meta"][name]:
                    priority = mixin.spec["meta"][name]["priority"]
                self.facade_index[f"{priority:02d}_{name}"] = self.facade(info["model"].facade)

    if "meta" in mixin.spec:
        klass.__init__ = __init__

    return klass


def _get_parse_method(method_base_name, method_info):
    method_type = method_info.get("parser", "variable")
    method = None

    def get_default_value(self):
        if "default_callback" in method_info:
            default_callback = getattr(self, method_info["default_callback"], None)
            if default_callback is None:
                raise CallbackNotExistsError(f"Command parameter default callback {default_callback} does not exist")
            return default_callback()
        return method_info.get("default", None)

    if method_type == "flag":

        def parse_flag(
            self,
            flag=method_info.get("flag", f"--{method_base_name}"),
            help_text=method_info.get("help", ""),
            tags=method_info.get("tags", None),
            system=method_info.get("system", False),
        ):
            self.parse_flag(method_base_name, flag=flag, help_text=help_text, system=system, tags=tags)

        method = parse_flag

    elif method_type == "variable":

        def parse_variable(
            self,
            optional=method_info.get("optional", f"--{method_base_name}"),
            help_text=method_info.get("help", ""),
            value_label=method_info.get("value_label", None),
            tags=method_info.get("tags", None),
            system=method_info.get("system", False),
        ):
            self.parse_variable(
                method_base_name,
                optional=optional,
                type=method_info.get("type", "str"),
                help_text=help_text,
                value_label=value_label,
                choices=method_info.get("choices", None),
                default=get_default_value(self),
                tags=tags,
                system=system,
            )

        method = parse_variable

    elif method_type == "variables":

        def parse_variables(
            self,
            optional=method_info.get("optional", f"--{method_base_name}"),
            help_text=method_info.get("help", ""),
            value_label=method_info.get("value_label", None),
            tags=method_info.get("tags", None),
            system=method_info.get("system", False),
        ):
            default_value = get_default_value(self)
            self.parse_variables(
                method_base_name,
                optional=optional,
                type=method_info.get("type", "str"),
                help_text=help_text,
                value_label=value_label,
                default=ensure_list(default_value) if default_value is not None else [],
                tags=tags,
                system=system,
            )

        method = parse_variables

    elif method_type == "fields":

        def parse_fields(
            self,
            optional=method_info.get("optional", False),
            help_callback=method_info.get("help_callback", None),
            callback_args=method_info.get("callback_args", None),
            callback_options=method_info.get("callback_options", None),
            tags=method_info.get("tags", None),
            system=method_info.get("system", False),
        ):
            facade = False
            if method_info.get("data", None):
                facade = model_index.Model(method_info["data"]).facade

            if help_callback:
                help_callback = getattr(self, help_callback, None)

            self.parse_fields(
                facade,
                method_base_name,
                optional=optional,
                help_callback=help_callback,
                callback_args=callback_args,
                callback_options=callback_options,
                tags=tags,
                system=system,
            )

        method = parse_fields

    else:
        raise ParseMethodNotSupportedError(f"Command parameter type {method_type} is not currently supported")

    method.__name__ = f"parse_{method_base_name}"
    return method


def _get_check_method(method_base_name, method_info):
    def method(self):
        if "default_callback" in method_info:
            default_callback = getattr(self, method_info["default_callback"], None)
            if default_callback is None:
                raise CallbackNotExistsError(f"Command parameter default callback {default_callback} does not exist")
            default_value = default_callback()
        else:
            default_value = method_info.get("default", None)

        if method_info["parser"] == "variables":
            values = self.options.get(method_base_name)
            if not default_value:
                return len(values) > 0

            return set(ensure_list(default_value)) != set(values)

        if default_value is None:
            return self.options.get(method_base_name) is not None

        return self.options.get(method_base_name) != default_value

    method.__name__ = f"check_{method_base_name}"
    return method


def _get_accessor_method(method_base_name, method_info):
    def accessor(self):
        value = self.options.get(method_base_name)

        if value is not None and method_info["parser"] == "variables":
            value = ensure_list(value)

        if "postprocessor" in method_info:
            postprocessor = getattr(self, method_info["postprocessor"], None)
            if postprocessor is None:
                raise CallbackNotExistsError(f"Command parameter postprocessor {postprocessor} does not exist")

            if value is not None:
                value = postprocessor(value)
        return value

    accessor.__name__ = method_base_name
    return property(accessor)


def _generate_resource_commands(command, name, spec):
    data_spec = settings.MANAGER.get_spec("data.{}".format(spec["resource"]))
    disabled_operations = ensure_list(data_spec.get("disable_ops", []))

    base_name = spec.get("base_name", name)
    roles_spec = data_spec.get("roles", {})
    meta_spec = data_spec.get("meta", {})
    options_spec = copy.deepcopy(spec.get("options", {}))

    if "allow_list" not in options_spec:
        options_spec["allow_list"] = "list" not in disabled_operations
    if "allow_access" not in options_spec:
        options_spec["allow_access"] = "retrieve" not in disabled_operations
    if "allow_update" not in options_spec:
        options_spec["allow_update"] = "update" not in disabled_operations
    if "allow_remove" not in options_spec:
        options_spec["allow_remove"] = "destroy" not in disabled_operations
    if "allow_clear" not in options_spec:
        options_spec["allow_clear"] = "clear" not in disabled_operations

    if meta_spec and "provider_name" in meta_spec:
        options_spec["provider_name"] = meta_spec["provider_name"]

    if "edit" in roles_spec:
        options_spec["edit_roles"] = roles_spec["edit"]

    if "view" in roles_spec:
        options_spec["view_roles"] = roles_spec["view"]

    resource.ResourceCommandSet(command, BaseCommand(spec["base"]), base_name, spec["resource"], **options_spec)


def display_command_info(klass, prefix="", display_function=logger.info, properties=True, methods=True):
    display_function(f"{prefix}{klass.__name__}")
    for parent in klass.__bases__:
        display_command_info(parent, f"{prefix}  << ", display_function)

    if properties:
        display_function(f"{prefix} properties:")
        for attribute in dir(klass):
            if not attribute.startswith("__") and not callable(getattr(klass, attribute)):
                display_function(f"{prefix}  ->  {attribute}")

    if methods:
        display_function(f"{prefix} methods:")
        for attribute in dir(klass):
            if not attribute.startswith("__") and callable(getattr(klass, attribute)):
                display_function(f"{prefix}  **  {attribute}")
