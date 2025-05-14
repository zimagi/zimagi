import copy
from pydoc import locate

from django.conf import settings
from utility.data import load_json


class GeneratorError(Exception):
    pass


class PluginError(Exception):
    pass


class ParamSchema:
    def __init__(self):
        self.clear()

    def clear(self):
        self.schema = {"requirements": [], "options": []}

    def require(self, type, name, help, config_name):
        if name in self.schema["options"]:
            return
        if name not in self.schema["requirements"]:
            self.schema["requirements"].append({"type": type, "name": name, "help": help, "config_name": config_name})

    def option(self, type, name, default, help, config_name):
        self.schema["options"].append(
            {"type": type, "name": name, "default": default, "help": help, "config_name": config_name}
        )

    def export(self):
        return self.schema


class BasePlugin:
    @classmethod
    def generate(cls, plugin, generator):
        def get_config(name, default):
            def config_accessor(self):
                return self.config.get(name, default)

            return property(config_accessor)

        for config_type in ("requirement", "option"):
            for name, info in plugin.meta.get(config_type, {}).items():
                setattr(plugin, f"field_{name}", get_config(name, info.get("default", None)))

        def check_system(cls):
            return generator.spec["system"]

        if "system" in generator.spec:
            plugin.check_system = classmethod(check_system)

    def __init__(self, type, name, command=None):
        self.name = name
        self.command = command
        self.errors = []

        self.config = {}

        self.schema = ParamSchema()
        self.provider_type = type
        self.provider_options = self.manager.index.get_plugin_providers(self.provider_type)

        self.test = False
        self.create_op = False

    def __eq__(self, other):
        if self.provider_type != other.provider_type or self.name != other.name:
            return False

        def is_equal(first, second):
            if isinstance(first, dict):
                if not isinstance(second, dict):
                    return False

                for key, value in first.items():
                    if key not in second:
                        return False

                    if not is_equal(first[key], second[key]):
                        return False
                return True

            elif isinstance(first, (list, tuple)):
                if not isinstance(second, (list, tuple)) or len(first) != len(second):
                    return False

                for index, value in enumerate(first):
                    if not is_equal(first[index], second[index]):
                        return False

                return True

            else:
                return first == second

        return is_equal(self.config, other.config)

    @property
    def manager(self):
        return settings.MANAGER

    @classmethod
    def check_system(cls):
        # Override in subclass
        return False

    def import_config(self, config):
        self.provider_schema()
        schema = self.schema.export()

        for requirement in schema["requirements"]:
            name = requirement["name"]

            if name not in config:
                error_message = f"Configuration {name} required for plugin provider {self.provider_type} {self.name}"
                if self.command:
                    self.command.error(error_message)
                else:
                    raise PluginError(error_message)

            value = config[name] if isinstance(config[name], requirement["type"]) else requirement["type"](config[name])
            self.config[name] = value

        for option in schema["options"]:
            name = option["name"]

            if name not in config:
                value = copy.deepcopy(option["default"])
            else:
                value = config[name] if isinstance(config[name], option["type"]) else option["type"](config[name])

            self.config[name] = value

    def provider_config(self):
        config_names = []

        for name, info in self.meta.get("requirement", {}).items():
            info = copy.deepcopy(info)
            self.requirement(locate(info.pop("type")), name, **info)
            config_names.append(name)

        for name, info in self.meta.get("option", {}).items():
            info = copy.deepcopy(info)
            self.option(locate(info.pop("type")), name, **info)
            config_names.append(name)

        for name in list(self.config.keys()):
            if name not in config_names:
                self.config.pop(name)

    def provider_schema(self):
        self.schema.clear()
        self.provider_config()
        return self.schema.export()

    def get_fields(self):
        schema = self.provider_schema()
        fields = []
        for field_type, field_data in schema.items():
            for field_info in field_data:
                fields.append(field_info["name"])
        return fields

    def get_config_fields(self):
        schema = self.provider_schema()
        fields = []
        for field_type, field_data in schema.items():
            for field_info in field_data:
                fields.append(field_info["name"])
        return fields

    def requirement(self, type, name, callback=None, callback_args=None, help=None, config_name=None):
        if not callback_args:
            callback_args = []

        config_value = self.command.get_config(config_name) if self.command else None

        def set_data(values, args):
            if values.get(name, None) is None:
                if config_value is not None:
                    values[name] = config_value
                elif self.create_op:
                    self.errors.append(f"Field '{name}' required when adding {self.name} instances")

            if name in values and values[name] is not None:
                values[name] = self.parse_value(type, values[name])

            if self.create_op and callback and callable(callback):
                args = [args] if not isinstance(args, (list, tuple)) else args
                callback(name, values[name], self.errors, *args)

        self.schema.require(type, name, help, config_name)
        set_data(self.config, callback_args)

    def option(self, type, name, default=None, callback=None, callback_args=None, help=None, config_name=None):
        if not callback_args:
            callback_args = []

        config_value = self.command.get_config(config_name) if self.command else None

        def set_data(values, args):
            process = True
            if values.get(name, None) is None:
                if config_value is not None:
                    values[name] = config_value
                else:
                    values[name] = default
                    process = False

            if values[name] is not None:
                values[name] = self.parse_value(type, values[name])

            if process and callback and callable(callback):
                args = [args] if not isinstance(args, (list, tuple)) else args
                callback(name, values[name], self.errors, *args)

        self.schema.option(type, name, default, help, config_name)
        set_data(self.config, callback_args)

    def parse_value(self, type, value):
        if isinstance(value, type):
            return value

        if type == int:
            return int(value)
        if type == float:
            return float(value)
        if type == str:
            return str(value)
        if type == bool:
            return load_json(value.lower())
        if type == list:
            return [x.strip() for x in value.split(",")]
        if type == dict:
            return load_json(value)

    def validate(self):
        if self.errors:
            error_message = "\n".join(self.errors)
            if self.command:
                self.command.error(error_message)
            else:
                raise PluginError(error_message)

    def field_help(self, type, exclude_fields=None):
        help = [" "]

        def render(messages="", prefix=""):
            if not isinstance(messages, (tuple, list)):
                messages = [messages]

            for message in messages:
                help.append(f"{prefix}{message}")

        for name, provider_class in self.provider_options.items():
            provider = provider_class(self.provider_type, name, self.command)
            schema = provider.provider_schema()

            render("-" * 40)
            render(("provider: {}".format(self._color_text("relation", name)), " "))

            if schema["requirements"]:
                render("provider requirements:", "  ")
                for require in schema["requirements"]:
                    if exclude_fields and require["name"] in exclude_fields:
                        continue

                    param_help = "{}".format(self._color_text("warning", require["name"]))

                    if require["config_name"]:
                        param_help += " (@{})".format(self._color_text("key", require["config_name"]))

                    param_help += " - {}".format(require["help"])
                    render(param_help, "    ")
                render()

            if schema["options"]:
                render("provider options:", "  ")
                for option in schema["options"]:
                    if exclude_fields and option["name"] in exclude_fields:
                        continue

                    param_help = ["{}".format(self._color_text("warning", option["name"]))]

                    if self.command and option["config_name"]:
                        default = self.command.get_config(option["config_name"])
                        if default is None:
                            config_label = self._color_text("key", option["config_name"])
                            default = option["default"]
                        else:
                            config_label = self._color_text("success", option["config_name"])

                        if default is not None:
                            param_help[0] += " (@{} | {})".format(config_label, self._color_text("value", default))
                        else:
                            param_help[0] += f" (@{config_label})"

                    elif option["default"] is not None:
                        param_help[0] += " ({})".format(self._color_text("value", option["default"]))

                    param_help.append("   - {}".format(option["help"]))
                    render(param_help, "    ")
            render()

        return help

    def run_list(self, items, callback):
        if not self.command:
            return None
        return self.command.run_list(items, callback)

    def run_exclusive(self, lock_id, callback, error_on_locked=False, timeout=600, interval=2):
        if not self.command:
            return None
        return self.command.run_exclusive(
            lock_id, callback, error_on_locked=error_on_locked, timeout=timeout, interval=interval
        )

    def _color_text(self, type, text):
        if self.command:
            return getattr(self.command, f"{type}_color")(text)
        else:
            return text
