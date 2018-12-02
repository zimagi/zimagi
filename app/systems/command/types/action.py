
from django.conf import settings
from django.core.management.base import CommandError

from systems.command import base
from systems.command.mixins.data import environment as mixins
from utility.display import print_table

import sh
import json


class ActionCommand(
    mixins.EnvironmentMixin, 
    base.AppBaseCommand
):
    def __init__(self, stdout=None, stderr=None, no_color=False):
        super().__init__(stdout, stderr, no_color)
        self.parser = None
        self.sh = sh

        self.options = {}
        self.schema = {}
        self.generate_schema()


    def generate_schema(self):
        pass

    def get_schema(self):
        return self.schema


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
        self.options = options

        environment = self.get_env()
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
