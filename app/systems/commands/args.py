
from django.core.management.base import CommandError

from rest_framework import serializers

import argparse
import re
import json


class SingleValue(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None):
        values = values[0] if isinstance(values, (list, tuple)) else values
        setattr(namespace, self.dest, values)

class SingleCSVValue(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None):
        values = values[0] if isinstance(values, (list, tuple)) else values
        setattr(namespace, self.dest, values.split(','))

class MultiValue(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None):
        if not values:
            values = []
        setattr(namespace, self.dest, values)

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

def parse_vars(parser, name, type, help_text, optional = False):
    type = get_type(type)
    if parser:
        nargs = '*' if optional else '+'
        parser.add_argument(
            name,
            action = MultiValue,
            nargs = nargs,
            type = type,
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

def parse_csv_option(parser, name, flags, help_text, value_label = None, default = None):
    if parser:
        flags = [flags] if isinstance(flags, str) else flags
        parser.add_argument(
            *flags,
            dest = name,
            action = SingleCSVValue,
            default = default,
            type = str,
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

def parse_bool(parser, name, flags, help_text):
    if parser:
        flags = [flags] if isinstance(flags, str) else flags
        parser.add_argument(
            *flags,
            dest = name,
            action = 'store_true',
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
