
from django.core.management.base import CommandError
from rest_framework import serializers

from utility.data import ensure_list

import argparse
import re


class SingleValue(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None):
        values = values[0] if isinstance(values, (list, tuple)) else values
        setattr(namespace, self.dest, values)

class SingleCSVValue(argparse.Action):
    def __init__(self, option_strings, dest, inner_type = None, **kwargs):
        super().__init__(option_strings, dest, **kwargs)
        self.inner_type = inner_type
        self.default = ensure_list(self.default) if self.default else []

    def __call__(self, parser, namespace, values, option_string = None):
        values = values[0] if isinstance(values, (list, tuple)) else values
        arg_values = []

        for value in values.split(','):
            arg_values.append(self.inner_type(value))

        setattr(namespace, self.dest, arg_values)

class MultiValue(argparse.Action):
    def __init__(self, option_strings, dest, **kwargs):
        super().__init__(option_strings, dest, **kwargs)
        self.default = ensure_list(self.default) if self.default else []

    def __call__(self, parser, namespace, values, option_string = None):
        arg_values = []
        if not values:
            values = []

        for value in ensure_list(values):
            arg_values.append(self.type(value))

        setattr(namespace, self.dest, arg_values)

class KeyValues(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None):
        options = {}

        if values:
            for key_value in values:
                components = key_value.split("=")
                key = components.pop(0)
                value = "=".join(components)
                options[key] = value

        setattr(namespace, self.dest, options)


def get_type(type):
    if callable(type):
        return type
    elif type == 'str':
        return str
    elif type == 'int':
        return int
    elif type == 'float':
        return float
    elif type == 'bool':
        return bool
    elif type == 'list':
        return list
    elif type == 'dict':
        return dict
    else:
        raise CommandError("Unsupported field type: {}".format(type))

def get_field(type, **options):
    if type == str:
        return serializers.CharField(**options)
    elif type == int:
        return serializers.IntegerField(**options)
    elif type == float:
        return serializers.FloatField(**options)
    elif type == bool:
        return serializers.BooleanField(**options)
    elif type == list:
        return serializers.ListField(**options)
    elif type == dict:
        return serializers.DictField(**options)
    else:
        raise CommandError("Unsupported field type: {}".format(type))


def parse_var(parser, name, type, help_text, optional = False, default = None, choices = None):
    type = get_type(type)
    if parser:
        nargs = '?' if optional else 1
        parser.add_argument(
            name,
            action = SingleValue,
            nargs = nargs,
            type = type,
            default = default,
            choices = choices,
            help = help_text
        )
    return get_field(type,
        required = not optional,
        label = name,
        help_text = re.sub(r'\s+', ' ', help_text)
    )

def parse_vars(parser, name, type, help_text, optional = False, default = None):
    type = get_type(type)
    if parser:
        nargs = '*' if optional else '+'
        parser.add_argument(
            name,
            action = MultiValue,
            nargs = nargs,
            type = type,
            default = default,
            help = help_text
        )
    return get_field(list,
        required = not optional,
        label = "JSON encoded {}".format(name),
        help_text = re.sub(r'\s+', ' ', help_text),
        child = get_field(type)
    )

def parse_option(parser, name, flags, type, help_text, value_label = None, default = None, choices = None):
    type = get_type(type)
    if parser:
        flags = [flags] if isinstance(flags, str) else flags
        parser.add_argument(
            *flags,
            dest = name,
            action = SingleValue,
            type = type,
            default = default,
            choices = choices,
            metavar = value_label,
            help = help_text
        )
    return get_field(type,
        required = False,
        label = name,
        help_text = re.sub(r'\s+', ' ', help_text)
    )

def parse_csv_option(parser, name, flags, type, help_text, value_label = None, default = None):
    type = get_type(type)
    if parser:
        flags = [flags] if isinstance(flags, str) else flags
        parser.add_argument(
            *flags,
            dest = name,
            action = SingleCSVValue,
            default = default,
            type = str,
            inner_type = type,
            metavar = "{},...".format(value_label),
            help = help_text
        )
    return get_field(list,
        required = False,
        label = "Comma separated {}".format(name),
        help_text = re.sub(r'\s+', ' ', help_text)
    )

def parse_options(parser, name, flags, type, help_text, value_label = None, default = None, choices = None):
    type = get_type(type)
    if parser:
        flags = [flags] if isinstance(flags, str) else flags
        parser.add_argument(
            *flags,
            dest = name,
            action = MultiValue,
            type = type,
            default = default,
            choices = choices,
            nargs = '+',
            metavar = value_label,
            help = help_text
        )
    return get_field(list,
        required = False,
        label = "JSON encoded {}".format(name),
        help_text = re.sub(r'\s+', ' ', help_text)
    )

def parse_bool(parser, name, flags, help_text, default = None):
    if parser:
        flags = [flags] if isinstance(flags, str) else flags
        parser.add_argument(
            *flags,
            dest = name,
            action = 'store_true',
            default = default,
            help = help_text
        )
    return get_field(bool,
        required = False,
        label = name,
        help_text = re.sub(r'\s+', ' ', help_text)
    )

def parse_key_values(parser, name, help_text, value_label = None, optional = False):
    if parser:
        nargs = '*' if optional else '+'
        parser.add_argument(
            name,
            action = KeyValues,
            nargs = nargs,
            metavar = value_label,
            help = help_text
        )
    return get_field(dict,
        required = not optional,
        label = "JSON encoded {}".format(name),
        help_text = re.sub(r'\s+', ' ', help_text)
    )
