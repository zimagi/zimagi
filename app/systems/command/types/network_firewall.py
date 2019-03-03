from settings import Roles
from .network import NetworkRouterCommand, NetworkActionCommand


class NetworkFirewallRouterCommand(NetworkRouterCommand):

    def get_priority(self):
        return 50


class NetworkFirewallActionCommand(NetworkActionCommand):

    def get_priority(self):
        return 50

    def groups_allowed(self):
        return super().groups_allowed() + [
            Roles.security_admin
        ]

