from django.conf import settings

import multiprocessing
import shutil


class MetaRuntime(type):

    def save(self, name, value):
        with self.process_lock:
            self.config[name] = value
            return self.config[name]

    def get(self, name, default = None):
        with self.process_lock:
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

    def system_command(self, value = None):
        return self.get_or_set('system_command', value, False)

    def admin_user(self, value = None):
        return self.get_or_set('admin_user', value)

    def active_user(self, value = None):
        return self.get_or_set('active_user', value)


class Runtime(object, metaclass = MetaRuntime):
    process_lock = multiprocessing.Lock()
    config = {}
