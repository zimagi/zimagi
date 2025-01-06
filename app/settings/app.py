from django.apps.config import AppConfig
from django.conf import settings


class AppInit(AppConfig):
    name = "zimagi"

    def ready(self):
        settings.MANAGER.index.generate()
