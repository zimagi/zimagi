import re

from systems.plugins.index import BaseProvider
from utility.data import create_token
from utility.time import Time


class Provider(BaseProvider("worker", "kubernetes")):
    @property
    def cluster(self):
        return self.manager.cluster

    def scale_agents(self, count):
        self.cluster.scale_agent(
            self.field_worker_type, self.agent_name.replace("_", "-"), re.split(r"\s+", self.field_command_name), count
        )

    def get_worker_count(self):
        return len(self.cluster.get_active_workers(self.field_worker_type))

    def ensure(self):
        def ensure_worker():
            time = Time(date_format="%Y-%m-%d", time_format="%H-%M-%S", spacer="-")
            self.start_worker(
                "{}-{}-{}".format(
                    self.field_worker_type,
                    time.now_string,
                    create_token(4, upper=False)[1:],
                )
            )

        if self.connection():
            self.command.run_exclusive("ensure_workers", ensure_worker)

    def start_worker(self, name):
        self.cluster.create_worker(self.field_worker_type, name.replace("_", "-"))
