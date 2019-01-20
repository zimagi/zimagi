from settings import Roles
from .user import UserActionCommand


class UserGroupActionCommand(UserActionCommand):

    def groups_allowed(self):
        return super().groups_allowed() + [
            Roles.user_group_admin
        ]
