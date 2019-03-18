from django.conf import settings

from systems.command.types import module
from systems.command.mixins import db

import json


class Command(
    db.DatabaseMixin,
    module.ModuleActionCommand
):
    def get_command_name(self):
        return 'sync'

    def get_priority(self):
        return -100

    def exec(self):
        self.silent_data('modules', self.db.save('module', encrypted = False))

    def postprocess(self, result):
        self.db.load(result.get_named_data('modules'), encrypted = False)

        for module in self.get_instances(self._module):
            module.provider.update()

        self.success('Modules successfully synced from remote environment')
