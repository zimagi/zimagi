from django.conf import settings

from settings.roles import Roles
from systems.command.action import ActionCommand
from systems.command.mixins.command.db import DatabaseMixin


class Command(
    DatabaseMixin,
    ActionCommand
):
    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.db_admin,
            Roles.processor_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 95

    def parse(self):
        self.parse_db_packages()

    def interpolate_options(self):
        return False

    def exec(self):
        self.silent_data('db', self.db.save(self.db_packages, encrypted = False))

    def postprocess(self, result):
        self.db.load(result.get_named_data('db'), encrypted = False)
        self.success("Database packages {} successfully pulled".format(",".join(self.db_packages)))
