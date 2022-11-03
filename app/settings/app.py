from django.conf import settings
from django.apps.config import AppConfig

from utility.environment import Environment

import os


class AppInit(AppConfig):
    name = 'zimagi'


    def ready(self):
        self.ensure_directories()
        settings.MANAGER.index.generate()


    def ensure_directories(self):
        setattr(settings, 'LIB_DIR', os.path.join(settings.ROOT_LIB_DIR, Environment.get_active_env()))
        for setting_name, directory in settings.PROJECT_PATH_MAP.items():
            setattr(settings, setting_name, os.path.join(settings.LIB_DIR, directory))
