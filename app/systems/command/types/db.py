from settings.roles import Roles
from .router import RouterCommand
from .action import ActionCommand
from systems.command.mixins import db


class DatabaseRouterCommand(RouterCommand):

    def get_priority(self):
        return 95


class DatabaseActionCommand(
    db.DatabaseMixin,
    ActionCommand
):

    def groups_allowed(self):
        return [
            Roles.admin,
            Roles.db_admin
        ]

    def server_enabled(self):
        return True

    def get_priority(self):
        return 95
