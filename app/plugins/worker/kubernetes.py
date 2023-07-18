from systems.plugins.index import BaseProvider
from utility.data import create_token
from utility.time import Time

import re


class Provider(BaseProvider('worker', 'kubernetes')):

    @property
    def cluster(self):
        return self.manager.cluster


    def check_agent(self, agent_name):
        return self.cluster.check_agent(self.field_worker_type, agent_name)

    def start_agent(self, agent_name):
        self.cluster.create_agent(
            self.field_worker_type,
            agent_name,
            re.split(r'\s+', self.field_command_name)
        )

    def stop_agent(self, agent_name):
        self.cluster.destroy_agent(self.field_worker_type, agent_name)


    def get_worker_count(self):
        return len(self.cluster.get_active_workers(self.field_worker_type))


    def ensure(self):
        def ensure_worker():
            time = Time(
                date_format = "%Y-%m-%d",
                time_format = "%H-%M-%S",
                spacer = '-'
            )
            self.start_worker("{}-{}-{}".format(self.field_worker_type, time.now_string, create_token(4, upper = False)[1:]))

        if self.connection():
            self.command.run_exclusive('ensure_workers', ensure_worker)


    def start_worker(self, name):
        self.cluster.create_worker(self.field_worker_type, name)
