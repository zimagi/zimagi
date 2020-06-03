from django.conf import settings
from django.apps.config import AppConfig


class AppInit(AppConfig):
    name = 'zimagi'


    def ready(self):
        settings.MANAGER.index.generate()