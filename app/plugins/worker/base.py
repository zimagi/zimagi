from django.conf import settings

from systems.plugins.index import BasePlugin
from systems.celery.worker import RedisConnectionMixin

import math


class BaseProvider(RedisConnectionMixin, BasePlugin('worker')):

    def __init__(self, type, name, command, app, **config):
        super().__init__(type, name, command)

        self.app = app
        self.import_config(config)


    def get_task_ratio(self):
        return self.field_command_options['task_ratio']

    def get_task_count(self):
        return self.connection().llen(self.field_worker_type)

    def get_worker_count(self):
        return 0


    def ensure(self):
        def ensure_workers():
            count = self.check_workers()
            if count:
                self.start_workers(count)

        if self.connection():
            self.command.run_exclusive('ensure_workers', ensure_workers)


    def check_workers(self):
        worker_count = self.get_worker_count()
        count = (math.floor(self.get_task_count() / self.get_task_ratio()) - worker_count)

        if not worker_count or count > 0:
            return min(max(count, 1), settings.WORKER_MAX_COUNT)
        return 0


    def start_workers(self, count):
        def start(name):
            self.start_worker(name)

        self.command.run_list([
            "{}-{}".format(self.field_worker_type, (index + 1))
            for index in range(0, count)
        ], start)

    def start_worker(self, name):
        # Override in subclass
        pass
