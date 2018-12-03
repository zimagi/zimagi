
from django.conf import settings
from django.core.management.base import CommandError

from rest_framework.compat import coreapi, coreschema
from rest_framework.schemas.inspectors import field_to_schema

from systems.command import base
from systems.command.mixins.core import CoreMixin
from systems.command.mixins.data.environment import EnvironmentMixin
from systems.api.schema import command
from systems.api import client
from utility.display import print_table

import sh
import json
import re


class ActionCommand(
    CoreMixin,
    EnvironmentMixin, 
    base.AppBaseCommand
):
    def __init__(self, stdout = None, stderr = None, no_color = False):
        super().__init__(stdout, stderr, no_color)
        self.sh = sh

        self.schema = {}
        self.options = {}
        self.parser = None
        self.parse_base()

        self.api_exec = False


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

    def parse_base(self):
        self.parse_verbosity()
        self.parse_color()
        self.parse()

    def add_arguments(self, parser):
        super().add_arguments(parser)

        self.parser = parser
        self.parse_base()


    def exec(self):
        # Override in subclass
        pass

    def handle(self, *args, **options):
        env = self.get_env()
        
        if not self.api_exec and env and env.host and self.server_enabled():
            api = client.API(env.host, env.port, env.token)
            self.data("Environment", env.name)
            self.info(api.execute(self.get_full_name(), options))
        else:
            self.options = options
            self.exec()


    def print_table(self, data):
        print_table(data)
