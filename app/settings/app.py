from django.conf import settings
from django.apps.config import AppConfig


class AppInit(AppConfig):
    name = 'mcmi'


    def ready(self):
        settings.MANAGER.index.generate()