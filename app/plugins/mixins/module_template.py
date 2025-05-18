import os

from systems.plugins.index import ProviderMixin


class ModuleTemplateMixin(ProviderMixin("module_template")):
    def _provision_template(self, instance, test=False):
        if self.field_use_template:
            template_fields = self.field_template_fields if self.field_template_fields else {}
            template_fields["module_name"] = instance.name

            if not os.path.isfile(os.path.join(self.module_path(instance.name, False), "zimagi.yml")):
                self.command.provision_template(
                    instance, os.path.join("module", self.field_template_package), template_fields, display_only=test
                )
