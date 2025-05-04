from .base import BaseCommand, SubCommandMixin


class RouterCommand(SubCommandMixin, BaseCommand):

    def exec(self, argv):
        print(self.name)
        print(self.overview)
        print(self.description)
        print(self.priority)
        print(self.resource)
        print(self.commands)
        print(argv)
