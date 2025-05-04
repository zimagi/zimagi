from .base import BaseExecutable, SubCommandMixin


class HelpCommand(SubCommandMixin, BaseExecutable):

    def __init__(self, client, schema):
        super().__init__(client, schema)
        self.title = schema.title
        self.description = schema.description

    def exec(self, argv):
        print(self.commands)
        print(self.title)
        print(self.description)
        print(argv)
