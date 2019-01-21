from settings import Roles
from .config import ConfigActionCommand


class ConfigGroupActionCommand(ConfigActionCommand):

    def groups_allowed(self):
        return super().groups_allowed() + [
            Roles.config_group_admin
        ]
