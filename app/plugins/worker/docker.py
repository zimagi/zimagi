from systems.plugins.index import BaseProvider


class Provider(BaseProvider('worker', 'docker')):

    def start_worker(self):
        self.command.manager.stop_service('worker', remove = True)

        service_spec = self.command.manager.get_service_spec('worker')
        service_spec['environment']['ZIMAGI_WORKER_TYPE'] = self.field_worker_type

        self.command.manager.start_service('worker', **service_spec)

    def check_worker(self):
        return self.command.manager.get_service('worker', restart = False, create = False)
