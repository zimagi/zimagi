from settings import Roles
from .server import ServerActionCommand


class ServerGroupActionCommand(ServerActionCommand):

    def groups_allowed(self):
        return super().groups_allowed() + [
            Roles.server_group_admin
        ]
