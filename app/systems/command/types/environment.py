from .action import ActionCommand


class EnvironmentActionCommand(ActionCommand):

    def server_enabled(self):
        return False

    def get_priority(self):
        return 10
