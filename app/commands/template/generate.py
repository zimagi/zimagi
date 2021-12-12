from systems.commands.index import Command


class Generate(Command('template.generate')):

    def exec(self):
        self.provision_template(
            self.module,
            self.module_template,
            self.template_fields,
            display_only = self.display_only
        )
