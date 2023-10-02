from django.conf import settings

from systems.plugins.index import BasePlugin
from systems.celery.worker import RedisConnectionMixin
from utility.data import create_token
from utility.time import Time

import math
import re


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


    def check_agents(self):
        state_key = "agent-{}".format(self.agent_name)
        agent_names = []

        for agent_name in self.command.get_state(state_key, []):
            if self.check_agent(agent_name):
                agent_names.append(agent_name)
            else:
                self.stop_agent(agent_name)

        self.command.set_state(state_key, agent_names)
        return agent_names

    def check_agent(self, agent_name):
        raise NotImplementedError("Method check_agent must be implemented in subclasses")


    def scale_agents(self, count):
        count = int(count)
        state_key = "agent-{}".format(self.agent_name)
        running_agents = self.check_agents()
        running_agent_count = len(running_agents)
        time = Time(
            date_format = '%Y%m%d',
            time_format = '%H%M%S',
            spacer = ''
        )

        def add_agent(index):
            agent_name = "{}-{}-{}".format(self.agent_name, time.now_string, create_token(4, upper = False))
            self.command.notice("Starting agent {} at {}".format(agent_name, self.command.time.now_string))
            self.start_agent(agent_name)
            running_agents.append(agent_name)

        def remove_agent(index):
            agent_name = running_agents.pop(0)
            self.command.notice("Stopping agent {} at {}".format(agent_name, self.command.time.now_string))
            self.stop_agent(agent_name)

        try:
            if running_agent_count < count:
                self.command.run_list(range(running_agent_count, count), add_agent)
            elif running_agent_count > count:
                self.command.run_list(range(running_agent_count, count, -1), remove_agent)
        finally:
            self.command.set_state(state_key, running_agents)

    def start_agent(self, agent_name):
        raise NotImplementedError("Method start_agent must be implemented in subclasses")

    def stop_agent(self, agent_name):
        raise NotImplementedError("Method stop_agent must be implemented in subclasses")


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
