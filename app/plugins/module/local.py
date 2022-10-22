from systems.plugins.index import BaseProvider
from utility.filesystem import remove_dir

import pathlib
import os


class Provider(BaseProvider('module', 'local')):

    def initialize_instance(self, instance, created):
        instance.remote = None
        instance.reference = 'development'


    def store_related(self, instance, created, test):
        if created:
            self._provision_template(instance, test)


    def finalize_instance(self, instance):
        def finalize():
            module_path = self.module_path(instance.name)
            remove_dir(pathlib.Path(module_path))

        self.run_exclusive("local-finalize-{}".format(instance.name), finalize)
