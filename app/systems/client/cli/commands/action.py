from systems.commands.args import get_type

from .base import BaseCommand


class ActionCommand(BaseCommand):

    def __init__(self, index, schema):
        super().__init__(index, schema)
        self.fields = schema.fields

    def parse(self):
        for field in self.fields:
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

    def exec(self):
        self.client.execute(self.name, **self.options)
