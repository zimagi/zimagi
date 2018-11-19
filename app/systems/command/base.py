
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class ComplexCommand(BaseCommand):
    
    def __init__(self, stdout=None, stderr=None, no_color=False):
        super(ComplexCommand, self).__init__(stdout, stderr, no_color)

    
    def add_arguments(self, parser):
        pass


    def handle(self, *args, **options):
        pass
