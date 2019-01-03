from .environment import EnvironmentRouterCommand, EnvironmentActionCommand


class ConfigRouterCommand(EnvironmentRouterCommand):

    def get_priority(self):
        return 10


class ConfigActionCommand(EnvironmentActionCommand):

    def server_enabled(self):
        return True

    def get_priority(self):
        return 10
