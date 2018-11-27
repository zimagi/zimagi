from django.core.management.base import BaseCommand
from db_mutex.models import DBMutex


class Command(BaseCommand):

    def handle(self, *args, **options):
        DBMutex.objects.all().delete()
