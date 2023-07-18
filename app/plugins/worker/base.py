from django.conf import settings

from systems.plugins.index import BasePlugin
from systems.celery.worker import RedisConnectionMixin

import math


class BaseProvider(RedisConnectionMixin, BasePlugin('worker')):

    def __init__(self, type, name, command, app, **config):
        super().__init__(type, name, command)

        self.app = app
        self.import_config(config)


    @property
    def agent_name(self):
        if not getattr(self, '_agent_name', None):
            self._agent_name = "-".join(re.split(r'\s+', self.field_command_name))
        return self._agent_name


    def _check_agents(self, callback):
        index = 1
        active = 0

        while True:
            if callback("{}-{}".format(self.agent_name, index)):
                active += 1
            else:
                break
            index += 1

        return active


    def scale_agents(self, count):
        agents_running = self._check_agents()

        if agents_running < count:
            for index in range(agents_running, count):
                agent_name = "{}-{}".format(self.agent_name, index + 1)
                self.command.notice("Starting agent {} at {}".format(agent_name, self.command.time.now_string))
                self.start_agent(agent_name)

        elif agents_running > count:
            for index in range(agents_running, count, -1):
                agent_name = "{}-{}".format(self.agent_name, index)
                self.command.notice("Stopping agent {} at {}".format(agent_name, self.command.time.now_string))
                self.stop_agent(agent_name)


    def start_agent(self, agent_name):
        # Override in subclass
        pass

    def stop_agent(self, agent_name):
        # Override in subclass
        pass


    def get_task_ratio(self):
        return self.field_command_options.get('task_ratio', settings.WORKER_TASK_RATIO)

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
