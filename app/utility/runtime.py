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
        self.store_env(name, False)
        self.store_repo(repo, False)
        self.store_image(image, False)
        Config.save(settings.RUNTIME_PATH, self.data)

    def store(self, name, value, default, save = True):
        if value:
            self.data[name] = value
        elif name not in self.data:
            self.data[name] = default
        if save:
            Config.save(settings.RUNTIME_PATH, self.data)

    def store_env(self, value, save = True):
        self.store('CENV_ENV', value, settings.DEFAULT_ENV_NAME, save)

    def store_repo(self, value, save = True):
        self.store('CENV_REPO', value, settings.DEFAULT_RUNTIME_REPO, save)

    def store_image(self, value, save = True):
        self.store('CENV_IMAGE', value, settings.DEFAULT_RUNTIME_IMAGE, save)

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

    def get_or_set(self, name, value = None, default = None):
        if value is not None:
            return self.save(name, value)
        return self.get(name, default)


    def api(self, value = None):
        return self.get_or_set('api', value)

    def debug(self, value = None):
        return self.get_or_set('debug', value, settings.DEBUG)

    def parallel(self, value = None):
        return self.get_or_set('parallel', value, settings.PARALLEL)

    def color(self, value = None):
        return self.get_or_set('color', value, settings.DISPLAY_COLOR)

    def width(self, value = None):
        columns, rows = shutil.get_terminal_size(fallback = (settings.DISPLAY_WIDTH, 25))
        return self.get_or_set('width', value, columns)

    def system_command(self, value = None):
        return self.get_or_set('system_command', value, False)

    def curr_env(self, value = None):
        return self.get_or_set('curr_env', value)

    def admin_user(self, value = None):
        return self.get_or_set('admin_user', value)

    def active_user(self, value = None):
        return self.get_or_set('active_user', value)


class Runtime(object, metaclass = MetaRuntime):
    lock = threading.Lock()
    data = {}
    config = {}
