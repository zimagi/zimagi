import zimagi


zimagi.settings.COMMAND_RAISE_ERROR = True


class TestError(Exception):
    pass


class BaseTest(object):

    def __init__(self, command, host):
        self.command = command
        self.host = host
        self.api = host.api(message_callback = self.message_callback)

    def message_callback(self, message):
        message.display()

    def exec(self):
        raise NotImplementedError("Subclasses of BaseTest must implement exec method")

