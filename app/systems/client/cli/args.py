from systems.commands import args
from utility.data import ensure_list


def parse_var(parser, name, type, help_text, optional=False, default=None, choices=None):
    if parser:
        type = args.get_type(type)
        nargs = "?" if optional else 1
        parser.add_argument(
            name, action=args.SingleValue, nargs=nargs, type=type, default=default, choices=choices or None, help=help_text
        )


def parse_vars(parser, name, type, help_text, optional=False, default=None):
    if parser:
        type = args.get_type(type)
        nargs = "*" if optional else "+"
        parser.add_argument(
            name, action=args.MultiValue, nargs=nargs, type=type, default=default if default else [], help=help_text
        )


def parse_option(parser, name, flags, type, help_text, value_label=None, default=None, choices=None):
    if parser:
        type = args.get_type(type)
        flags = [flags] if isinstance(flags, str) else flags
        parser.add_argument(
            *flags,
            dest=name,
            action=args.SingleValue,
            type=type,
            default=default,
            choices=choices or None,
            metavar=value_label,
            help=help_text,
        )


def parse_csv_option(parser, name, flags, type, help_text, value_label=None, default=None):
    if parser:
        type = args.get_type(type)
        flags = [flags] if isinstance(flags, str) else flags
        parser.add_argument(
            *flags,
            dest=name,
            action=args.SingleCSVValue,
            default=default if default else [],
            type=str,
            inner_type=type,
            metavar=f"{value_label},...",
            help=help_text,
        )


def parse_options(parser, name, flags, type, help_text, value_label=None, default=None, choices=None):
    if parser:
        type = args.get_type(type)
        flags = [flags] if isinstance(flags, str) else flags
        parser.add_argument(
            *flags,
            dest=name,
            action=args.MultiValue,
            type=type,
            default=default,
            choices=choices or None,
            nargs="+",
            metavar=value_label,
            help=help_text,
        )


def parse_bool(parser, name, flags, help_text, default=False):
    if parser:
        flags = [flags] if isinstance(flags, str) else flags
        parser.add_argument(*flags, dest=name, action="store_true", default=default, help=help_text)


def parse_key_values(parser, name, help_text, value_label=None, optional=False):
    if parser:
        nargs = "*" if optional else "+"
        parser.add_argument(name, action=args.KeyValues, nargs=nargs, metavar=value_label, help=help_text)


class CommandArgumentMixin:

    def parse_flag(self, name, flag, help_text, config_name=None, default=False):
        if config_name:
            help_text = f"[@{self.key_color(config_name)}] {help_text}"
        if default:
            help_text = f"{help_text} <{self.value_color("True")}>"

        parse_bool(
            self.parser,
            name,
            flag,
            help_text,
            default=default,
        )

    def parse_variable(
        self,
        name,
        optional,
        type,
        help_text,
        value_label=None,
        config_name=None,
        default=None,
        choices=None,
    ):
        if optional:
            if config_name:
                help_text = f"[@{self.key_color(config_name)}] {help_text}"
            if default:
                help_text = f"{help_text} <{self.value_color(default)}>"

        if optional and isinstance(optional, (str, list, tuple)):
            if not value_label:
                value_label = name

            parse_option(
                self.parser,
                name,
                optional,
                type,
                help_text,
                value_label=value_label,
                default=default,
                choices=choices,
            )
        else:
            parse_var(
                self.parser,
                name,
                type,
                help_text,
                optional=optional,
                default=default,
                choices=choices,
            )

    def parse_variables(self, name, optional, type, help_text, value_label=None, config_name=None, default=None):
        if default is None:
            default = []

        if optional:
            if config_name:
                help_text = f"[@{self.key_color(f"option_{name}")}] {help_text}"
            if default:
                help_text = f"{help_text} <{self.value_color(", ".join(ensure_list(default)))}>"

        if optional and isinstance(optional, (str, list, tuple)):
            if not value_label:
                value_label = name

            parse_csv_option(
                self.parser,
                name,
                optional,
                type,
                help_text,
                value_label=value_label,
                default=default,
            )
        else:
            parse_vars(
                self.parser,
                name,
                type,
                help_text,
                optional=optional,
                default=default,
            )

    def parse_fields(
        self,
        name,
        help_text,
        value_label=None,
        optional=False,
    ):
        parse_key_values(self.parser, name, help_text, value_label=value_label, optional=optional)
