from django.conf import settings

from utility.config import Config

import os


class MetaRuntime(type):

    def get_db_path(self):
        return "{}.db".format(settings.BASE_DATA_PATH)


    def get_env(self):
        if not self.data:
            self.data = Config.load(settings.RUNTIME_PATH, {})
        return self.data.get('CENV_ENV', settings.DEFAULT_ENV_NAME)


    def set_env(self, name = None, repo = None, image = None):
        self.store('CENV_ENV', name, settings.DEFAULT_ENV_NAME)
        self.store('CENV_REPO', repo, settings.DEFAULT_RUNTIME_REPO)
        self.store('CENV_IMAGE', image, settings.DEFAULT_RUNTIME_IMAGE)
        Config.save(settings.RUNTIME_PATH, self.data)

    def store(self, name, value, default):
        if value:
            self.data[name] = value 
        elif name not in self.data:
            self.data[name] = default


    def delete_env(self):
        os.remove(settings.RUNTIME_PATH)


class Runtime(object, metaclass = MetaRuntime):
    data = {}
