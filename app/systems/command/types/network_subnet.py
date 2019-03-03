from settings import Roles
from .network import NetworkRouterCommand, NetworkActionCommand


class NetworkSubnetRouterCommand(NetworkRouterCommand):

    def get_priority(self):
        return 55


class NetworkSubnetActionCommand(NetworkActionCommand):

    def get_priority(self):
        return 55

