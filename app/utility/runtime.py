from django.conf import settings

import threading
import shutil
import copy


class Runtime(object):

    def __init__(self, config = None):
        self.lock = threading.Lock()
        self.config = config if isinstance(config, dict) else {}


    def clone(self):
        return Runtime(copy.deepcopy(self.config))


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


    def debug(self, value = None):
        return self.get_or_set('debug', value, settings.DEBUG)

    def parallel(self, value = None):
        return self.get_or_set('parallel', value, settings.PARALLEL)

    def color(self, value = None):
        return self.get_or_set('color', value, settings.DISPLAY_COLOR)

    def width(self, value = None):
        columns, rows = shutil.get_terminal_size(fallback = (settings.DISPLAY_WIDTH, 25))
        return self.get_or_set('width', value, columns)


    def admin_user(self, value = None):
        return self.get_or_set('admin_user', value)

    def active_user(self, value = None):
        return self.get_or_set('active_user', value)
