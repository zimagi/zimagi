from django.conf import settings

from .config import Config

import os
import threading
import shutil


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


    def save(self, name, value):
        with self.lock:
            self.config[name] = value
            return self.config[name]

    def get(self, name, default = None):
        with self.lock:
            if name not in self.config:
                return default
            else:
                return self.config[name]


    def api(self, value = None):
        if value is not None:
            return self.save('api', value)
        return self.get('api')

    def debug(self, value = None):
        if value is not None:
            return self.save('debug', value)
        return self.get('debug', settings.DEBUG)

    def parallel(self, value = None):
        if value is not None:
            return self.save('parallel', value)
        return self.get('parallel', settings.PARALLEL)

    def color(self, value = None):
        if value is not None:
            return self.save('color', value)
        return self.get('color', settings.DISPLAY_COLOR)

    def width(self, value = None):
        if value is not None:
            return self.save('width', value)

        columns, rows = shutil.get_terminal_size(fallback = (settings.DISPLAY_WIDTH, 25))
        return self.get('width', columns)

    def admin_user(self, value = None):
        if value is not None:
            return self.save('admin_user', value)
        return self.get('admin_user', None)

    def active_user(self, value = None):
        if value is not None:
            return self.save('active_user', value)
        return self.get('active_user', None)


class Runtime(object, metaclass = MetaRuntime):
    lock = threading.Lock()
    data = {}
    config = {}
