import re

from django.conf import settings
from systems.commands.args import get_type

from ..errors import CommandAbort
from .base import BaseCommand


class ActionCommand(BaseCommand):

    def parse(self):
        for field in self.schema.fields:
            if field.name not in ["json_options"]:
                if field.method == "flag":
                    self.parse_flag(
                        field.name, field.argument, field.description, config_name=field.config, default=field.default
                    )
                elif field.method == "variable":
                    self.parse_variable(
                        field.name,
                        field.argument if field.argument else not field.required,
                        get_type(field.type),
                        field.description,
                        value_label=field.value_label,
                        config_name=field.config,
                        default=field.default,
                        choices=field.choices,
                    )
                elif field.method == "variables":
                    self.parse_variables(
                        field.name,
                        field.argument if field.argument else not field.required,
                        get_type(field.type),
                        field.description,
                        value_label=field.value_label,
                        config_name=field.config,
                        default=field.default,
                    )
                elif field.method == "fields":
                    self.parse_fields(
                        field.name,
                        field.description,
                        value_label=field.value_label,
                        optional=not field.required,
                    )

    def confirmation(self):
        if "--force" not in self.args:
            message = "Are you absolutely sure?"
            confirmation = input(f"{message} (type YES to confirm): ")

            if not re.match(r"^[Yy][Ee][Ss]$", confirmation):
                raise CommandAbort("User aborted")

    def exec(self):
        if self.schema.confirm:
            self.confirmation()

        self.client.execute(self.name, **self.options)

    def handle_message(self, message):
        message.display(debug=settings.DEBUG, width=settings.DISPLAY_WIDTH)
