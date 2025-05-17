import math
import re

from django.conf import settings
from systems.celery.worker import RedisConnectionMixin
from systems.plugins.index import BasePlugin
from utility.data import create_token
from utility.time import Time


class BaseProvider(RedisConnectionMixin, BasePlugin("worker")):
    def __init__(self, type, name, command, app, **config):
        super().__init__(type, name, command)

        self.app = app
        self.import_config(config)

    @property
    def agent_name(self):
        if not getattr(self, "_agent_name", None):
            self._agent_name = "-".join(re.split(r"\s+", self.field_command_name))
        return self._agent_name

    def check_agents(self):
        state_key = f"agent-{self.agent_name}"
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
        state_key = f"agent-{self.agent_name}"
        running_agents = self.check_agents()
        running_agent_count = len(running_agents)
        time = Time(date_format="%Y%m%d", time_format="%H%M%S", spacer="")

        def add_agent(index):
            token = create_token(4, upper=False)
            agent_name = f"{self.agent_name}-{time.now_string}-{token}"
            self.command.notice(f"Starting agent {agent_name} at {self.command.time.now_string}")
            self.start_agent(agent_name)
            running_agents.append(agent_name)

        def remove_agent(index):
            agent_name = running_agents.pop(0)
            self.command.notice(f"Stopping agent {agent_name} at {self.command.time.now_string}")
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

    def get_task_capacity(self):
        return self.field_command_options.get("task_capacity", settings.WORKER_TASK_CAPACITY)

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
            self.command.run_exclusive("ensure_workers", ensure_workers)

    def check_workers(self):
        worker_count = self.get_worker_count()
        task_count = self.get_task_count()
        task_capacity = self.get_task_capacity()
        worker_scaling = math.floor(task_count / task_capacity) - worker_count
        workers_created = 0

        worker_metrics = {
            "name": self.name,
            "provider": self.provider_type,
            "worker_max_count": settings.WORKER_MAX_COUNT,
            "worker_count": worker_count,
            "task_count": task_count,
            "task_capacity": task_capacity,
            "worker_scaling": worker_scaling,
            "workers_created": 0,
        }
        if not worker_count or worker_scaling > 0:
            workers_created = min(max(worker_scaling, 1), settings.WORKER_MAX_COUNT)
            worker_metrics["workers_created"] = workers_created

        self.command.send("worker:scaling", worker_metrics)
        return workers_created

    def start_workers(self, count):
        time = Time(date_format="%Y%m%d", time_format="%H%M%S", spacer="")

        def start(name):
            self.start_worker(name)

        self.command.run_list(
            [
                f"worker-{self.field_worker_type}-{time.now_string}-{create_token(4, upper=False)}"
                for index in range(0, count)
            ],
            start,
        )

    def start_worker(self, name):
        # Override in subclass
        pass
