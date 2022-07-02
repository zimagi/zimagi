from systems.plugins.index import BaseProvider
from utility.filesystem import remove_dir

import pathlib
import os


class Provider(BaseProvider('module', 'local')):

    def initialize_instance(self, instance, created):
        instance.remote = None
        instance.reference = 'development'


    def store_related(self, instance, created, test):
        module_path = self.module_path(instance.name, False)

        if not os.path.isdir(module_path) and created and self.field_use_template:
            template_fields = self.field_template_fields if self.field_template_fields else {}
            template_fields['module_name'] = instance.name

            self.command.provision_template(
                instance,
                os.path.join('module', self.field_template_package),
                template_fields,
                display_only = test
            )


    def finalize_instance(self, instance):
        def finalize():
            module_path = self.module_path(instance.name)
            remove_dir(pathlib.Path(module_path))

        self.run_exclusive("local-finalize-{}".format(instance.name), finalize)
