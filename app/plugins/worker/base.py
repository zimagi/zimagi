from systems.plugins.index import BasePlugin
from systems.celery.worker import RedisConnectionMixin

import threading


class BaseProvider(RedisConnectionMixin, BasePlugin('worker')):

    thread_lock = threading.Lock()


    def __init__(self, type, name, command, **config):
        super().__init__(type, name, command)
        self.import_config(config)


    def ensure(self):
        with self.thread_lock:
            if self.connection() and not self.check_worker():
                self.start_worker()


    def check_worker(self):
        # Override in subclass
        return False

    def start_worker(self):
        # Override in subclass
        pass
