
from django.conf import settings
from django.core.management.base import CommandError

from rest_framework.compat import coreapi, coreschema
from rest_framework.schemas.inspectors import field_to_schema

from systems.command import base
from systems.command.mixins.data import environment as mixins
from systems.api.schema import command
from systems.api import client
from utility.display import print_table

import sh
import json
import re


class ActionCommand(
    mixins.EnvironmentMixin, 
    base.AppBaseCommand
):
    def __init__(self, stdout=None, stderr=None, no_color=False):
        super().__init__(stdout, stderr, no_color)
        self.sh = sh

        self.options = {}
        self.schema = {}

        self.parser = None
        self.parse()


    def add_schema_field(self, name, field, optional = True):
        self.schema[name] = coreapi.Field(
            name = name,
            location = 'form',
            required = not optional,
            schema = field_to_schema(field)
        )

    def get_schema(self):
        return command.CommandSchema(list(self.schema.values()), re.sub(r'\s+', ' ', self.get_description(False)))


    def parse(self):
        # Override in subclass
        pass

    def add_arguments(self, parser):
        super().add_arguments(parser)

        self.parser = parser
        self.parse()

    def get_options(self, input):
        schema = self.get_schema()
        options = {}

        for name, value in input.items():
            if name in schema:
                options[name] = getattr(self, "_render_{}".format(schema[name]))(value)

        return options


    def exec(self):
        # Override in subclass
        pass

    def handle(self, *args, **options):
        env = self.get_env()

        self.options = options
        self.exec()


    def print_table(self, data):
        print_table(data)

    
    def _render_str(self, value):
        if isinstance(value, (tuple, list)):
            return str(value[0])
        return str(value)

    def _render_list(self, value):
        if not isinstance(value, (tuple, list)):
            value = [value]
        return list(value)

    def _render_dict(self, value):
        if isinstance(value, (tuple, list)):
            value = value[0]
        return json.loads(value)
