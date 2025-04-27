from systems.commands.index import Command


class Create(Command("module.create")):

    def parse(self, add_api_fields=False):
        super().parse(add_api_fields)
        self.parse_scope(self._module)
        self.parse_relations(self._module)

    def exec(self):
        self.set_scope(self._module)
        self.module_provider.create(
            self.module_key,
            {
                "template_package": self.module_template,
                "template_fields": self.template_fields,
                **self.get_relations(self._module),
            },
        )
