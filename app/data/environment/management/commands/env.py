
from django.core.management.base import CommandError

from systems.command import ComplexCommand


class Command(ComplexCommand):
    
    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)


    def handle(self, *args, **options):
        super(Command, self).handle(*args, **options)
