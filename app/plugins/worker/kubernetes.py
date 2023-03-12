from systems.plugins.index import BaseProvider


class Provider(BaseProvider('worker', 'kubernetes')):

    @property
    def cluster(self):
        return self.manager.cluster


    def get_worker_count(self):
        return len(self.cluster.get_active_workers(self.field_worker_type))

    def start_worker(self, name):
        self.cluster.create_worker(self.field_worker_type, name)
