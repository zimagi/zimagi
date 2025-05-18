import re

from systems.plugins.index import BaseProvider


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

    def start_worker(self, name):
        self.cluster.create_worker(self.field_worker_type, name.replace("_", "-"))
