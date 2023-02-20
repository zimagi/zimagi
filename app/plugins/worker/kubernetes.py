from systems.plugins.index import BaseProvider


class Provider(BaseProvider('worker', 'kubernetes')):

    def check_worker(self):
        return False

    def start_worker(self):
        pass
