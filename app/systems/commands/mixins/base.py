from data.base.id_resource import IdentifierResourceBase
from django.conf import settings
from systems.commands import args
from utility import data, text

from .meta import MetaBaseMixin


class BaseMixin(metaclass=MetaBaseMixin):
    @classmethod
    def generate(cls, command, generator):
        # Override in subclass if needed
        pass

    def parse_flag(self, name, flag, help_text, default=False, tags=None, system=False):
        with self.option_lock:
            if name not in self.option_map:
                cli_help_text = help_text
                flag_default = self.options.get_default(name)
                if flag_default is None:
                    flag_default = default

                if flag_default:
                    option_label = self.success_color(f"option_{name}")
                    default_value_text = self.value_color("True")

                    cli_help_text = f"{help_text} <{default_value_text}>"

                    if settings.MCP_EXEC:
                        help_text = f"{help_text} <DEFAULT: {default_value_text}>"
                else:
                    option_label = self.key_color(f"option_{name}")

                args.parse_bool(
                    self.parser if not system else None,
                    name,
                    flag,
                    f"[@{option_label}] {cli_help_text}",
                    default=flag_default,
                )
                self.add_schema_field(
                    "flag",
                    name,
                    type=bool,
                    argument=flag,
                    config=f"option_{name}",
                    help_text=help_text,
                    default=flag_default,
                    optional=True,
                    system=system,
                    tags=tags,
                )
                if flag_default is not None:
                    self.option_defaults[name] = flag_default

                self.option_map[name] = True

    def parse_variable(
        self,
        name,
        optional,
        type,
        help_text,
        value_label=None,
        default=None,
        choices=None,
        tags=None,
        system=False,
    ):
        with self.option_lock:
            if name not in self.option_map:
                variable_default = None
                cli_help_text = help_text

                if optional:
                    variable_default = self.options.get_default(name)
                    if variable_default is not None:
                        option_label = self.success_color(f"option_{name}")
                    else:
                        option_label = self.key_color(f"option_{name}")
                        variable_default = default

                    if variable_default is None:
                        default_label = ""
                    else:
                        default_value_text = self.value_color(variable_default)

                        if settings.MCP_EXEC:
                            default_label = f" <DEFAULT: {default_value_text}>"
                        else:
                            default_label = f" <{default_value_text}>"

                    cli_help_text = f"[@{option_label}] {help_text} {default_label}".strip()

                    if settings.MCP_EXEC and default_label:
                        help_text = f"{help_text} {default_label}"

                if optional and isinstance(optional, (str, list, tuple)):
                    if not value_label:
                        value_label = name

                    args.parse_option(
                        self.parser if not system else None,
                        name,
                        optional,
                        type,
                        cli_help_text,
                        value_label=value_label.upper(),
                        default=variable_default,
                        choices=choices,
                    )
                    self.add_schema_field(
                        "variable",
                        name,
                        type=type,
                        argument=optional,
                        config=f"option_{name}",
                        help_text=help_text,
                        value_label=value_label,
                        default=variable_default,
                        choices=choices,
                        optional=True,
                        system=system,
                        tags=tags,
                    )
                else:
                    args.parse_var(
                        self.parser if not system else None,
                        name,
                        type,
                        cli_help_text,
                        optional=optional,
                        default=variable_default,
                        choices=choices,
                    )
                    self.add_schema_field(
                        "variable",
                        name,
                        type=type,
                        argument=None,
                        config=f"option_{name}" if optional else None,
                        help_text=help_text,
                        value_label=value_label,
                        default=variable_default,
                        choices=choices,
                        optional=optional,
                        system=system,
                        tags=tags,
                    )
                if variable_default is not None:
                    self.option_defaults[name] = variable_default

                self.option_map[name] = True

    def parse_variables(self, name, optional, type, help_text, value_label=None, default=None, tags=None, system=False):
        if default is None:
            default = []

        with self.option_lock:
            if name not in self.option_map:
                variable_default = None
                cli_help_text = help_text

                if optional:
                    variable_default = self.options.get_default(name)
                    if variable_default is not None:
                        option_label = self.success_color(f"option_{name}")
                    else:
                        option_label = self.key_color(f"option_{name}")
                        variable_default = default

                    if not variable_default:
                        default_label = ""
                    else:
                        default_value_text = self.value_color(", ".join(data.ensure_list(variable_default)))

                        if settings.MCP_EXEC:
                            default_label = f" <DEFAULT: {default_value_text}>"
                        else:
                            default_label = f" <{default_value_text}>"

                    cli_help_text = f"[@{option_label}] {help_text} {default_label}".strip()

                    if settings.MCP_EXEC and default_label:
                        help_text = f"{help_text} {default_label}"

                if optional and isinstance(optional, (str, list, tuple)):
                    comma_separated_label = "(comma separated)"
                    cli_help_text = f"{cli_help_text} {comma_separated_label}"
                    help_text = f"{help_text} {comma_separated_label}"

                    if not value_label:
                        value_label = name

                    args.parse_csv_option(
                        self.parser if not system else None,
                        name,
                        optional,
                        type,
                        cli_help_text,
                        value_label=value_label.upper(),
                        default=variable_default,
                    )
                    self.add_schema_field(
                        "variables",
                        name,
                        type=type,
                        argument=optional,
                        config=f"option_{name}",
                        help_text=help_text,
                        value_label=value_label,
                        default=variable_default,
                        optional=True,
                        system=system,
                        tags=tags,
                    )
                else:
                    args.parse_vars(
                        self.parser if not system else None,
                        name,
                        type,
                        cli_help_text,
                        optional=optional,
                        default=variable_default,
                    )
                    self.add_schema_field(
                        "variables",
                        name,
                        type=type,
                        argument=None,
                        config=f"option_{name}" if optional else None,
                        help_text=help_text,
                        value_label=value_label,
                        default=variable_default,
                        optional=optional,
                        system=system,
                        tags=tags,
                    )
                if variable_default is not None:
                    self.option_defaults[name] = variable_default

                self.option_map[name] = True

    def parse_fields(
        self,
        facade,
        name,
        optional=False,
        help_callback=None,
        callback_args=None,
        callback_options=None,
        exclude_fields=None,
        tags=None,
        system=False,
    ):
        with self.option_lock:
            if not callback_args:
                callback_args = []
            if not callback_options:
                callback_options = {}

            if exclude_fields:
                exclude_fields = data.ensure_list(exclude_fields)
                callback_options["exclude_fields"] = exclude_fields

            if name not in self.option_map:
                value_label = "field=VALUE"

                if facade:
                    help_text = "\n".join(self.field_help(name, facade, exclude_fields))
                else:
                    help_text = f"\nfields as key value pairs ({name})\n"

                if help_callback and callable(help_callback):
                    help_text += "\n".join(help_callback(*callback_args, **callback_options))

                args.parse_key_values(
                    self.parser if not system else None, name, help_text, value_label=value_label, optional=optional
                )
                self.add_schema_field(
                    "fields",
                    name,
                    type=None,
                    argument=None,
                    config=None,
                    help_text=help_text,
                    value_label=value_label,
                    default=None,
                    optional=optional,
                    system=system,
                    tags=tags,
                )
                self.option_defaults[name] = {}
                self.option_map[name] = True

    def parse_test(self):
        self.parse_flag("test", "--test", "test execution without permanent changes", tags=["system"])

    @property
    def test(self):
        return self.options.get("test")

    def parse_force(self):
        self.parse_flag("force", "--force", "force execution even with provider errors", tags=["system"])

    @property
    def force(self):
        return self.options.get("force")

    def parse_count(self):
        self.parse_variable(
            "count", "--count", int, "instance count (default 1)", value_label="COUNT", default=1, tags=["list", "limit"]
        )

    @property
    def count(self):
        return self.options.get("count")

    def parse_clear(self):
        self.parse_flag("clear", "--clear", "clear all items", tags=["system"])

    @property
    def clear(self):
        return self.options.get("clear")

    def parse_search(self, optional=True, help_text="one or more search queries"):
        self.parse_variables("instance_search_query", optional, str, help_text, value_label="REFERENCE", tags=["search"])
        self.parse_flag("instance_search_or", "--or", "perform an OR query on input filters", tags=["search"])

    @property
    def search_queries(self):
        return self.options.get("instance_search_query")

    @property
    def search_join(self):
        join_or = self.options.get("instance_search_or")
        return "OR" if join_or else "AND"

    def field_help(self, name, facade, exclude_fields=None):
        field_index = facade.field_index
        system_fields = [x.name for x in facade.system_field_instances]
        show_key = False

        if issubclass(facade.model, IdentifierResourceBase) and facade.key() == facade.pk:
            show_key = True

        lines = [f"fields as key value pairs ({name})", ""]

        lines.append("-" * 40)
        lines.append("model requirements:")
        for name in facade.required_fields:
            if exclude_fields and name in exclude_fields:
                continue

            if (show_key or name not in system_fields) and not name.endswith("_ptr"):
                field = field_index[name]
                field_label = type(field).__name__.replace("Field", "").lower()
                if field_label == "char":
                    field_label = "string"

                choices = []
                if field.choices:
                    choices = [self.value_color(x[0]) for x in field.choices]

                lines.append(
                    "    {} {}{}".format(
                        self.warning_color(field.name), field_label, ":> " + ", ".join(choices) if choices else ""
                    )
                )
                if field.help_text:
                    lines.extend(
                        (
                            "",
                            "       - {}".format("\n".join(text.wrap(field.help_text, 40, indent="         "))),
                        )
                    )
        lines.append("")

        lines.append("model options:")
        for name in facade.optional_fields:
            if exclude_fields and name in exclude_fields:
                continue

            if name not in system_fields:
                field = field_index[name]
                field_label = type(field).__name__.replace("Field", "").lower()
                if field_label == "char":
                    field_label = "string"

                choices = []
                if field.choices:
                    choices = [self.value_color(x[0]) for x in field.choices]

                default = facade.get_field_default(field)

                if default is not None:
                    lines.append(
                        "    {} {} ({}){}".format(
                            self.warning_color(field.name),
                            field_label,
                            self.value_color(default),
                            ":> " + ", ".join(choices) if choices else "",
                        )
                    )
                else:
                    lines.append(
                        "    {} {} {}".format(
                            self.warning_color(field.name), field_label, ":> " + ", ".join(choices) if choices else ""
                        )
                    )

                if field.help_text:
                    lines.extend(
                        (
                            "",
                            "       - {}".format("\n".join(text.wrap(field.help_text, 40, indent="         "))),
                        )
                    )
        lines.append("")
        return lines
