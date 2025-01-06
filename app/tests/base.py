class BaseTest:
    def __init__(self, command, tags=None, exclude_tags=None):
        self.command = command
        self.manager = command.manager
        self.tags = tags or []
        self.exclude_tags = exclude_tags or []

    def exec(self):
        raise NotImplementedError("Subclasses of BaseTest must implement exec method")
