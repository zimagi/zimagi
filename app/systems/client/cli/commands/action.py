from .base import BaseCommand


class ActionCommand(BaseCommand):

    def __init__(self, client, schema):
        super().__init__(client, schema)
        self.fields = schema.fields

    def exec(self, argv):
        print(self.name)
        print(self.overview)
        print(self.description)
        print(self.priority)
        print(self.resource)
        print(self.fields)
        print(argv)
