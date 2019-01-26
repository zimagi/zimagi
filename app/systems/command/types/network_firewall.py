from settings import Roles
from .network import NetworkActionCommand


class NetworkFirewallActionCommand(NetworkActionCommand):

    def groups_allowed(self):
        return super().groups_allowed() + [
            Roles.security_admin
        ]

