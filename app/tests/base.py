
class BaseTest(object):

    def __init__(self, command):
        self.command = command
        self.manager = command.manager

    def exec(self):
        raise NotImplementedError("Subclasses of BaseTest must implement exec method")
