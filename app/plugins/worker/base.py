from django.conf import settings

from systems.plugins.index import BasePlugin
from systems.celery.worker import RedisConnectionMixin
from utility.data import ensure_list

import redis


class BaseProvider(RedisConnectionMixin, BasePlugin('worker')):

    def __init__(self, type, name, command, **config):
        super().__init__(type, name, command)
        self.import_config(config)


    def ensure(self):
        if self.connection() and \
            not self.check_worker():
            self.start_worker()

    def start_worker(self):
        # Override in subclass
        pass

    def check_worker(self):
        # Override in subclass
        return False
