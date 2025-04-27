from systems.commands.index import Command


class Add(Command("module.add")):

    def parse(self, add_api_fields=False):
        super().parse(add_api_fields)
        self.parse_scope(self._module)
        self.parse_relations(self._module)

        self.parse_module_fields(
            True, help_callback=self.get_provider("module", "help").field_help, exclude_fields=["remote"]
        )

    def exec(self):
        self.set_scope(self._module)
        self.module_fields["remote"] = self.remote
        self.module_provider.create(None, {**self.module_fields, **self.get_relations(self._module)})
